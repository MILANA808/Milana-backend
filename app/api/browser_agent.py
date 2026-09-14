"""AKSI Infinity browser computer-use runtime.

Provides an explicit, permission-gated browser session for navigation and UI actions.
The browser is an execution tool, not an unrestricted autonomous authority: callers must
set browser_actions=true, and UI-mutating actions require a task-scoped one-time approval token.
"""
from __future__ import annotations

import asyncio
import hashlib
import ipaddress
import secrets
import socket
from datetime import datetime, timezone
from typing import Any, Dict
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

try:
    from playwright.async_api import Browser, BrowserContext, Page, async_playwright
except ImportError:  # pragma: no cover
    Browser = BrowserContext = Page = Any
    async_playwright = None

from app.task_store import get as load_task, save as persist_task

router = APIRouter(prefix="/api/agent/browser", tags=["AKSI Browser"])
_SESSIONS: Dict[str, Dict[str, Any]] = {}
_LOCK = asyncio.Lock()


class BrowserCreate(BaseModel):
    browser_actions: bool = False
    headless: bool = True
    task_id: str = Field(min_length=1, max_length=200)


class NavigateRequest(BaseModel):
    url: str = Field(min_length=8, max_length=4096)


class ClickRequest(BaseModel):
    selector: str = Field(min_length=1, max_length=1000)
    approval_token: str = Field(min_length=16, max_length=200)


class TypeRequest(BaseModel):
    selector: str = Field(min_length=1, max_length=1000)
    text: str = Field(max_length=10000)
    submit: bool = False
    approval_token: str = Field(min_length=16, max_length=200)


def _safe_public_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise HTTPException(400, "Only public http(s) URLs are allowed")
    host = parsed.hostname.lower().rstrip(".")
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
        raise HTTPException(403, "Local/internal hosts are blocked")
    try:
        addresses = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM)
        for item in addresses:
            ip = ipaddress.ip_address(item[4][0])
            if not ip.is_global:
                raise HTTPException(403, "Private, loopback and link-local addresses are blocked")
    except socket.gaierror as exc:
        raise HTTPException(400, f"Unable to resolve host: {exc}") from exc
    return url


def _consume_approval(task_id: str, token: str, action: str) -> Dict[str, Any]:
    """Consume a single-use approval token for exactly one browser action."""
    task = load_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    for approval in task.get("approvals", []):
        if approval.get("token_hash") == token_hash and approval.get("status") == "GRANTED" and approval.get("action") == action:
            approval.update({"status": "CONSUMED", "consumed_at": datetime.now(timezone.utc).isoformat(), "token_hash": None})
            task["updated_at"] = datetime.now(timezone.utc).isoformat()
            persist_task(task)
            return approval
    raise HTTPException(403, "Invalid, revoked, already consumed, or action-mismatched approval token")


async def _session(session_id: str) -> Dict[str, Any]:
    session = _SESSIONS.get(session_id)
    if not session:
        raise HTTPException(404, "Browser session not found")
    return session


@router.post("/sessions")
async def create_browser_session(body: BrowserCreate):
    if not body.browser_actions:
        raise HTTPException(403, "browser_actions permission is required")
    if not load_task(body.task_id):
        raise HTTPException(404, "Task not found")
    if async_playwright is None:
        raise HTTPException(503, "Playwright is not installed")
    async with _LOCK:
        pw = await async_playwright().start()
        browser = await pw.chromium.launch(headless=body.headless)
        context = await browser.new_context()
        page = await context.new_page()
        sid = "aksi-browser-" + secrets.token_hex(8)
        _SESSIONS[sid] = {"pw": pw, "browser": browser, "context": context, "page": page, "task_id": body.task_id}
    return {"ok": True, "session_id": sid, "status": "READY", "capabilities": ["navigate", "click", "type", "read", "screenshot"], "task_id": body.task_id}


@router.post("/sessions/{session_id}/navigate")
async def navigate(session_id: str, body: NavigateRequest):
    session = await _session(session_id)
    url = _safe_public_url(body.url)
    page: Page = session["page"]
    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
    return {"ok": True, "url": page.url, "title": await page.title()}


@router.post("/sessions/{session_id}/click")
async def click(session_id: str, body: ClickRequest):
    session = await _session(session_id)
    _consume_approval(session["task_id"], body.approval_token, "browser.click")
    page: Page = session["page"]
    await page.locator(body.selector).first.click(timeout=15000)
    return {"ok": True, "url": page.url, "title": await page.title()}


@router.post("/sessions/{session_id}/type")
async def type_text(session_id: str, body: TypeRequest):
    session = await _session(session_id)
    _consume_approval(session["task_id"], body.approval_token, "browser.type")
    page: Page = session["page"]
    await page.locator(body.selector).first.fill(body.text, timeout=15000)
    if body.submit:
        await page.locator(body.selector).first.press("Enter")
    return {"ok": True, "url": page.url, "title": await page.title()}


@router.get("/sessions/{session_id}/read")
async def read_page(session_id: str):
    session = await _session(session_id)
    page: Page = session["page"]
    text = await page.locator("body").inner_text(timeout=15000)
    return {"ok": True, "url": page.url, "title": await page.title(), "text": text[:30000]}


@router.get("/sessions/{session_id}/screenshot")
async def screenshot(session_id: str):
    session = await _session(session_id)
    page: Page = session["page"]
    data = await page.screenshot(type="png")
    import base64
    return {"ok": True, "url": page.url, "png_base64": base64.b64encode(data).decode("ascii")}


@router.delete("/sessions/{session_id}")
async def close_browser_session(session_id: str):
    session = await _session(session_id)
    await session["context"].close()
    await session["browser"].close()
    await session["pw"].stop()
    _SESSIONS.pop(session_id, None)
    return {"ok": True, "status": "CLOSED"}
