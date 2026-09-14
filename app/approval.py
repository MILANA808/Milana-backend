"""Shared, task-scoped, one-time approval primitives for AKSI.

Approvals are intentionally action-scoped: a token granted for browser.click
cannot be replayed for browser.type or another task. The in-process lock closes
the obvious concurrent-consume race inside a single API worker.
"""
from __future__ import annotations

import asyncio
import hashlib
import secrets
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import HTTPException

from app.task_store import get as load_task, save as persist_task

_LOCK = asyncio.Lock()


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _task(task_id: str) -> Dict[str, Any]:
    task = load_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return task

async def request_approval(task_id: str, action: str, reason: str = "") -> Dict[str, Any]:
    async with _LOCK:
        task = _task(task_id)
        approval = {
            "id": "approval-" + secrets.token_hex(8),
            "action": action,
            "reason": reason,
            "status": "PENDING",
            "created_at": now(),
        }
        task.setdefault("approvals", []).append(approval)
        task["updated_at"] = now()
        persist_task(task)
        return approval

async def grant_approval(task_id: str, approval_id: str) -> str:
    async with _LOCK:
        task = _task(task_id)
        for approval in task.get("approvals", []):
            if approval.get("id") == approval_id:
                if approval.get("status") != "PENDING":
                    raise HTTPException(409, "Approval is not pending")
                token = "aksi-approval-" + secrets.token_urlsafe(24)
                approval.update({"status": "GRANTED", "token_hash": token_hash(token), "granted_at": now()})
                task["updated_at"] = now()
                persist_task(task)
                return token
        raise HTTPException(404, "Approval not found")

async def revoke_approval(task_id: str, approval_id: str) -> None:
    async with _LOCK:
        task = _task(task_id)
        for approval in task.get("approvals", []):
            if approval.get("id") == approval_id:
                approval.update({"status": "REVOKED", "token_hash": None, "revoked_at": now()})
                task["updated_at"] = now()
                persist_task(task)
                return
        raise HTTPException(404, "Approval not found")


def public_approvals(task_id: str):
    task = _task(task_id)
    return [{k: v for k, v in a.items() if k not in {"token", "token_hash"}} for a in task.get("approvals", [])]

async def consume_approval(task_id: str, token: str, action: str) -> Dict[str, Any]:
    """Atomically consume a granted token for exactly this task and action."""
    async with _LOCK:
        task = _task(task_id)
        digest = token_hash(token)
        for approval in task.get("approvals", []):
            if (approval.get("token_hash") == digest
                    and approval.get("status") == "GRANTED"
                    and approval.get("action") == action):
                approval.update({"status": "CONSUMED", "consumed_at": now(), "token_hash": None})
                task["updated_at"] = now()
                persist_task(task)
                return approval
        raise HTTPException(403, "Invalid, revoked, already consumed, or action-mismatched approval token")
