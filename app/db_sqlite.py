"""SQLite MVP for register/login (Phase 1). Swap to PostgreSQL in Phase 2."""
from __future__ import annotations

import hashlib
import os
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, Optional

DB_PATH = os.getenv("AKSI_SQLITE", "aksi_phase1.db")
SEED = os.getenv("RESONANCE_SEED", "Alfiya_AKSI_DIMAX_v3_2026")


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_pw(password: str, salt: str) -> str:
    return hashlib.sha256(f"{password}|{salt}|{SEED}".encode()).hexdigest()


@contextmanager
def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with connect() as c:
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
              id TEXT PRIMARY KEY,
              username TEXT UNIQUE NOT NULL,
              password_hash TEXT NOT NULL,
              salt TEXT NOT NULL,
              email TEXT,
              bio TEXT DEFAULT '',
              did TEXT,
              public_key TEXT,
              created_at TEXT NOT NULL,
              last_login TEXT,
              is_active INTEGER DEFAULT 1
            )
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS agents (
              did TEXT PRIMARY KEY,
              name TEXT,
              model TEXT,
              purpose TEXT,
              public_key TEXT,
              registered_at TEXT,
              reputation_score REAL DEFAULT 0.68,
              is_revoked INTEGER DEFAULT 0
            )
            """
        )


def register_user(username: str, password: str, email: str = "") -> Dict[str, Any]:
    username = username.strip().lower()
    if len(username) < 3:
        raise ValueError("username too short")
    if len(password) < 6:
        raise ValueError("password too short")
    salt = secrets.token_hex(8)
    uid = secrets.token_hex(12)
    did = f"did:aksi:user:{hashlib.sha256((username + uid).encode()).hexdigest()[:32]}"
    with connect() as c:
        try:
            c.execute(
                "INSERT INTO users (id, username, password_hash, salt, email, did, created_at) VALUES (?,?,?,?,?,?,?)",
                (uid, username, _hash_pw(password, salt), salt, email, did, _utc()),
            )
        except sqlite3.IntegrityError:
            raise ValueError("username taken")
    return {"id": uid, "username": username, "did": did}


def login_user(username: str, password: str) -> Dict[str, Any]:
    username = username.strip().lower()
    with connect() as c:
        row = c.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    if not row or not row["is_active"]:
        raise ValueError("invalid credentials")
    if _hash_pw(password, row["salt"]) != row["password_hash"]:
        raise ValueError("invalid credentials")
    with connect() as c:
        c.execute("UPDATE users SET last_login=? WHERE id=?", (_utc(), row["id"]))
    return {
        "id": row["id"],
        "username": row["username"],
        "did": row["did"],
        "email": row["email"],
        "bio": row["bio"] or "",
    }


def get_user(user_id: str) -> Optional[Dict[str, Any]]:
    with connect() as c:
        row = c.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    if not row:
        return None
    return {
        "id": row["id"],
        "username": row["username"],
        "did": row["did"],
        "email": row["email"],
        "bio": row["bio"] or "",
    }


def register_agent(name: str, model: str, purpose: str, public_key: str = "") -> Dict[str, Any]:
    did = f"did:aksi:agent:{hashlib.sha256((name + model + _utc()).encode()).hexdigest()[:32]}"
    with connect() as c:
        c.execute(
            "INSERT INTO agents (did, name, model, purpose, public_key, registered_at, reputation_score) VALUES (?,?,?,?,?,?,?)",
            (did, name, model, purpose, public_key, _utc(), 0.68),
        )
    return {"did": did, "name": name, "model": model, "purpose": purpose, "reputation_score": 0.68}


def list_agents() -> list:
    with connect() as c:
        rows = c.execute("SELECT * FROM agents WHERE is_revoked=0 ORDER BY registered_at DESC").fetchall()
    return [dict(r) for r in rows]
