"""Minimal admin API — users, agents, system stats"""
from __future__ import annotations

import os
from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from app import db_sqlite as db
from app.core.crypto import get_crypto
from app.core.reputation import compute_eqs

router = APIRouter(prefix="/api/admin", tags=["admin"])

ADMIN_TOKEN = os.getenv("AKSI_ADMIN_TOKEN", "aksi-admin-dev")


def _require_admin(authorization: Optional[str], x_admin_token: Optional[str]) -> None:
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    if x_admin_token:
        token = x_admin_token
    if token != ADMIN_TOKEN:
        raise HTTPException(401, "admin token required (AKSI_ADMIN_TOKEN)")


@router.get("/stats")
async def stats(
    authorization: Optional[str] = Header(None),
    x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token"),
):
    _require_admin(authorization, x_admin_token)
    agents = db.list_agents()
    return {
        "users_note": "sqlite users table",
        "agents": len(agents),
        "eqs": compute_eqs(),
        "did": get_crypto().get_did(),
        "service": "aksi-phase1-admin",
    }


@router.get("/users")
async def list_users(
    authorization: Optional[str] = Header(None),
    x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token"),
):
    _require_admin(authorization, x_admin_token)
    # expose via direct SQL
    import sqlite3
    from app.db_sqlite import DB_PATH

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, username, email, did, created_at, last_login, is_active FROM users"
    ).fetchall()
    conn.close()
    return {"users": [dict(r) for r in rows]}


class BlockBody(BaseModel):
    blocked: bool = True


@router.post("/users/{user_id}/block")
async def block_user(
    user_id: str,
    body: BlockBody,
    authorization: Optional[str] = Header(None),
    x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token"),
):
    _require_admin(authorization, x_admin_token)
    import sqlite3
    from app.db_sqlite import DB_PATH

    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE users SET is_active=? WHERE id=?",
        (0 if body.blocked else 1, user_id),
    )
    conn.commit()
    conn.close()
    return {"ok": True, "user_id": user_id, "blocked": body.blocked}


@router.get("/agents")
async def admin_agents(
    authorization: Optional[str] = Header(None),
    x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token"),
):
    _require_admin(authorization, x_admin_token)
    return {"agents": db.list_agents()}


@router.get("/system")
async def system_info(
    authorization: Optional[str] = Header(None),
    x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token"),
):
    _require_admin(authorization, x_admin_token)
    c = get_crypto()
    return {
        "did": c.get_did(),
        "stableHash": c.stable_hash(),
        "publicKeyB64": c.public_key_b64()[:40] + "…",
        "eqs": compute_eqs(),
        "admin": "token-gate",
    }
