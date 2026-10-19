"""Authentication and ownership checks for task-scoped API routes."""
from __future__ import annotations

from typing import Optional

from fastapi import Header, HTTPException
from app import db_sqlite as db


def require_user(authorization: Optional[str] = Header(None)) -> str:
    """Resolve an existing login session; fail closed for anonymous requests."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    token = authorization[7:].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    # The current login implementation owns the session registry. Import lazily
    # to avoid router-import cycles during FastAPI startup.
    try:
        from app.api_phase1 import _sessions
        user_id = _sessions.get(token)
        user = db.get_user(user_id) if user_id else None
    except Exception:
        user = None
        user_id = None
    if not user or not user_id or user.get("is_active", 1) in (False, 0):
        raise HTTPException(status_code=401, detail="Invalid or inactive session")
    return str(user_id)


def require_task_owner(task: dict, user_id: str) -> None:
    if not task or str(task.get("owner_id") or "") != str(user_id):
        # Do not reveal whether another user's task exists.
        raise HTTPException(status_code=404, detail="Task not found")
