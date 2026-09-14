"""AKSI Infinity web-agent runtime.

This is a bounded, auditable agent loop: plan -> search/open -> extract -> verify -> report.
Browser automation is optional (Playwright); public HTTP research works without it.
External side effects are never executed by this module: they require an explicit approval
boundary to be implemented by the caller.
"""
from __future__ import annotations

import asyncio
import hashlib
import re
import secrets
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/agent", tags=["AKSI Infinity Agent"])

TASKS: Dict[str, Dict[str, Any]] = {}
MAX_SOURCES = 20
MAX_PAGE_CHARS = 18000


class Permissions(BaseModel):
    internet: bool = True
    read_pages: bool = True
    browser_actions: bool = False
    downloads: bool = True
    external_actions: bool = False
    save_memory: bool = True


class TaskCreate(BaseModel):
    goal: str = Field(min_length=3, max_length=4000)
    permissions: Permissions = Permissions()
    max_sources: int = Field(default=8, ge=1, le=MAX_SOURCES)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def event(task: Dict[str, Any], message: str, status: str = "running") -> None:
    task["journal"].append({"at": now(), "message": message, "status": status})
    task["updated_at"] = now()


async def ddg_search(client: httpx.AsyncClient, query: str, limit: int) -> List[Dict[str, str]]:
    r = await client.get("https://html.duckduckgo.com/html/", params={"q": query}, headers={"User-Agent": "AKSI-Infinity/1.0"})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    out: List[Dict[str, str]] = []
    for a in soup.select("a.result__a")[:limit]:
        href = a.get("href")
        title = a.get_text(" ", strip=True)
        if href and title:
            out.append({"title": title, "url": href})
    return out


async def fetch_page(client: httpx.AsyncClient, url: str) -> Dict[str, Any]:
    r = await client.get(url, follow_redirects=True, headers={"User-Agent": "AKSI-Infinity/1.0"})
    content_type = r.headers.get("content-type", "")
    if "text/html" not in content_type:
        return {"url": str(r.url), "status": r.status_code, "text": "", "title": str(r.url)}
    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))[:MAX_PAGE_CHARS]
    return {"url": str(r.url), "status": r.status_code, "title": soup.title.get_text(strip=True) if soup.title else str(r.url), "text": text}


def make_plan(goal: str) -> List[str]:
    return [
        "Clarify the objective and success criteria",
        "Search the public web for relevant sources",
        "Open and extract evidence from the strongest sources",
        "Cross-check claims and record uncertainty",
        "Generate a structured report with sources",
        "Create an integrity receipt for the execution record",
    ]


def receipt(task: Dict[str, Any]) -> Dict[str, str]:
    payload = "|".join([task["id"], task["goal"], task["status"], *[s["url"] for s in task["sources"]]])
    return {"protocol": "AKSI-VAI/1", "hash": "sha256:" + hashlib.sha256(payload.encode()).hexdigest(), "timestamp": now()}


async def execute(task_id: str) -> None:
    task = TASKS[task_id]
    task["status"] = "PLANNING"
    event(task, "Задача принята. Формирую план.")
    task["plan"] = make_plan(task["goal"])
    if not task["permissions"].internet:
        task["status"] = "NEEDS_PERMISSION"
        event(task, "Для этой задачи требуется разрешение на интернет.", "blocked")
        return
    task["status"] = "RESEARCHING"
    event(task, "Интернет разрешён. Начинаю веб-исследование.")
    try:
        timeout = httpx.Timeout(15.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            results = await ddg_search(client, task["goal"], task["max_sources"])
            event(task, f"Найдено {len(results)} результатов поиска.")
            for result in results:
                if not task["permissions"].read_pages:
                    break
                try:
                    page = await fetch_page(client, result["url"])
                    if page["status"] < 400 and page["text"]:
                        task["sources"].append({**result, "status": page["status"], "text": page["text"]})
                        event(task, f"Прочитано: {page['title'][:120]}")
                except Exception as exc:
                    event(task, f"Не удалось прочитать {result['url']}: {type(exc).__name__}", "warning")
    except Exception as exc:
        task["status"] = "FAILED"
        event(task, f"Ошибка веб-runtime: {type(exc).__name__}: {exc}", "error")
        return

    task["status"] = "ANALYZING"
    event(task, "Источники собраны. Формирую факты и ограничения.")
    task["findings"] = [
        {"source": s["title"], "url": s["url"], "excerpt": s["text"][:700]} for s in task["sources"]
    ]
    task["status"] = "VERIFYING"
    event(task, "Проверяю наличие источников и отмечаю неопределённость.")
    task["verification"] = {
        "sources_count": len(task["sources"]),
        "independent_source_count": len({s["url"].split('/')[2] for s in task["sources"] if '://' in s["url"]}),
        "status": "supported" if task["sources"] else "insufficient_evidence",
        "note": "Наличие источника не означает истинность утверждения; выводы требуют проверки контекста.",
    }
    task["status"] = "COMPLETED"
    event(task, "Отчёт готов.", "completed")
    task["report"] = {
        "title": "AKSI Infinity — отчёт по задаче",
        "goal": task["goal"],
        "summary": f"Собрано источников: {len(task['sources'])}. Статус доказательной базы: {task['verification']['status']}.",
        "findings": task["findings"],
        "verification": task["verification"],
    }
    task["receipt"] = receipt(task)
    task["updated_at"] = now()


@router.post("/tasks")
async def create_task(body: TaskCreate, background_tasks: BackgroundTasks):
    task_id = "aksi-task-" + secrets.token_hex(8)
    task = {
        "id": task_id,
        "goal": body.goal,
        "status": "CREATED",
        "created_at": now(),
        "updated_at": now(),
        "permissions": body.permissions.model_dump(),
        "max_sources": body.max_sources,
        "plan": [], "journal": [], "sources": [], "findings": [], "verification": {}, "report": None, "receipt": None,
    }
    TASKS[task_id] = task
    background_tasks.add_task(execute, task_id)
    return {"ok": True, "task": task}


@router.get("/tasks/{task_id}")
async def get_task(task_id: str):
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return {"ok": True, "task": task}


@router.get("/tasks")
async def list_tasks(limit: int = 20):
    items = list(TASKS.values())[-max(1, min(limit, 100)):]
    return {"ok": True, "tasks": list(reversed(items))}


@router.post("/tasks/{task_id}/stop")
async def stop_task(task_id: str):
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    task["status"] = "STOPPED"
    event(task, "Выполнение остановлено пользователем.", "stopped")
    return {"ok": True, "task": task}
