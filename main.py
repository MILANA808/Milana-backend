"""
Milana-backend (AKSI) v0.8.0
Identity · Chat · Agents · Admin · World search · Codex · LLM · Memory · Resonance · Seal
Copyright (c) AKSI Project
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Dict, Any
import hashlib
import secrets
import re
import os
from collections import defaultdict
from pathlib import Path

try:
    import httpx
    HTTPX = True
except ImportError:
    HTTPX = False

try:
    from aksi.api import router as aksi_v2_router
    AKSI_V2_AVAILABLE = True
except ImportError:
    AKSI_V2_AVAILABLE = False
    aksi_v2_router = None

try:
    from app.api_phase1 import router as phase1_router
    from app.db_sqlite import init_db as phase1_init_db
    PHASE1_AVAILABLE = True
except ImportError:
    PHASE1_AVAILABLE = False
    phase1_router = None
    phase1_init_db = None

try:
    from app.api.chat import router as chat_router
    CHAT_AVAILABLE = True
except ImportError:
    CHAT_AVAILABLE = False
    chat_router = None

try:
    from app.api.admin import router as admin_router
    ADMIN_AVAILABLE = True
except ImportError:
    ADMIN_AVAILABLE = False
    admin_router = None

try:
    from app.api.identity import router as identity_router
    IDENTITY_AVAILABLE = True
except ImportError:
    IDENTITY_AVAILABLE = False
    identity_router = None

try:
    from app.api.agents import router as agents_router
    AGENTS_AVAILABLE = True
except ImportError:
    AGENTS_AVAILABLE = False
    agents_router = None

VERSION = "0.8.0"
CODEX = {
    "version": "1.0",
    "title": "Кодекс Суверенного ИИ АКСИ",
    "rules": [
        "Не выдумывать факты; указывать источники",
        "Признавать неуверенность",
        "Показывать ход рассуждения где уместно",
        "Отказ при вреде людям / эксплуатации",
        "Identity (DID) — ответственность, не маркетинг",
    ],
    "url": "https://milana808.github.io/CODEX.md",
}
BLOCK_PATTERNS = [
    (re.compile(r"как\s+(сделать|собрать).{0,40}(бомб|взрывчат|отрав)", re.I), "вред"),
    (re.compile(r"how\s+to\s+(make|build).{0,40}(bomb|explosive)", re.I), "harm"),
]
app = FastAPI(title="Milana-backend (AKSI)", description="Sovereign AI API · agents · search · codex · identity · llm · seal", version=VERSION)

# Wildcard CORS + credentials is an unsafe/invalid browser combination. Keep public
# reads broadly accessible but never advertise credentialed cross-origin requests.
_cors_origins = [x.strip() for x in os.getenv("AKSI_CORS_ORIGINS", "*").split(",") if x.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    from app.middleware.aksi_seal import AksiSealMiddleware
    app.add_middleware(AksiSealMiddleware)
    SEAL_MIDDLEWARE = True
except ImportError:
    SEAL_MIDDLEWARE = False

if AKSI_V2_AVAILABLE and aksi_v2_router:
    app.include_router(aksi_v2_router)
if PHASE1_AVAILABLE and phase1_router:
    app.include_router(phase1_router)
if CHAT_AVAILABLE and chat_router:
    app.include_router(chat_router)
if ADMIN_AVAILABLE and admin_router:
    app.include_router(admin_router)
if IDENTITY_AVAILABLE and identity_router:
    app.include_router(identity_router)
if AGENTS_AVAILABLE and agents_router:
    app.include_router(agents_router)

ADMIN_DIR = Path(__file__).parent / "admin"
if ADMIN_DIR.is_dir():
    app.mount("/admin-ui", StaticFiles(directory=str(ADMIN_DIR), html=True), name="admin-ui")

@app.on_event("startup")
async def _startup():
    if PHASE1_AVAILABLE and phase1_init_db:
        phase1_init_db()

logs_storage: List[dict] = []
proof_storage: List[dict] = []
ai_work_sessions: List[dict] = []
crypto_keys_storage: List[dict] = []
ai_code_metrics = {"total_sessions": 0, "total_code_changes": 0, "total_lines_modified": 0, "total_files_touched": 0, "total_commits": 0, "languages": defaultdict(int), "operations": defaultdict(int), "session_durations": [], "error_rate": 0.0, "success_rate": 100.0}
aksi_metrics = {"eqs": 0.72, "empathy_boost": 0.25, "grid_system": "3x3", "status": "active", "ai_code_work": ai_code_metrics}

class EchoRequest(BaseModel):
    message: str
class ProofStableRequest(BaseModel):
    signature: str
    timestamp: Optional[str] = None
    metrics: Optional[dict] = None
class LogAppendRequest(BaseModel):
    level: str
    message: str
    context: Optional[dict] = None
class AIWorkSessionRequest(BaseModel):
    session_id: Optional[str] = None
    action: str
    files_modified: Optional[List[str]] = None
    lines_changed: Optional[int] = None
    language: Optional[str] = None
    operation: Optional[str] = None
    commit_hash: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
class CryptoKeyRecordRequest(BaseModel):
    key_type: str
    public_key: str
    purpose: str
    algorithm: str
    created_by: str
    metadata: Optional[Dict[str, Any]] = None
class WorldSearchRequest(BaseModel):
    q: str
    include_arxiv: Optional[bool] = None
class CodexCheckRequest(BaseModel):
    text: str

def codex_check(text: str) -> dict:
    for pat, why in BLOCK_PATTERNS:
        if pat.search(text or ""):
            return {"ok": False, "reason": why, "codex": CODEX["version"]}
    return {"ok": True, "codex": CODEX["version"]}
