"""
Milana-backend (AKSI) v0.6.0
Identity · Chat · Admin · World search · Codex · LLM · Memory · Resonance
Copyright (c) Alfiia Bashirova
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Dict, Any
import hashlib
import secrets
import re
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

VERSION = "0.6.0"

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

app = FastAPI(
    title="Milana-backend (AKSI)",
    description="Sovereign AI API · search · codex · identity · llm",
    version=VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

ai_code_metrics = {
    "total_sessions": 0,
    "total_code_changes": 0,
    "total_lines_modified": 0,
    "total_files_touched": 0,
    "total_commits": 0,
    "languages": defaultdict(int),
    "operations": defaultdict(int),
    "session_durations": [],
    "error_rate": 0.0,
    "success_rate": 100.0,
}

aksi_metrics = {
    "eqs": 0.72,
    "empathy_boost": 0.25,
    "grid_system": "3x3",
    "status": "active",
    "ai_code_work": ai_code_metrics,
}


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


async def wiki_search(q: str) -> Optional[dict]:
    if not HTTPX:
        return None
    clean = re.sub(r"^(что такое|who is|what is|расскажи про)\s+", "", q, flags=re.I).strip()
    if not clean:
        return None
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(
                "https://ru.wikipedia.org/w/api.php",
                params={
                    "action": "opensearch",
                    "search": clean,
                    "limit": 1,
                    "namespace": 0,
                    "format": "json",
                },
            )
            data = r.json()
            title = data[1][0] if data and len(data) > 1 and data[1] else None
            if not title:
                return None
            s = await client.get(
                f"https://ru.wikipedia.org/api/rest_v1/page/summary/{title}"
            )
            js = s.json()
            extract = js.get("extract") or ""
            url = (js.get("content_urls") or {}).get("desktop", {}).get("page", "")
            return {
                "text": f"{js.get('title', title)}. {extract[:700]}",
                "source": "Wikipedia",
                "url": url,
            }
    except Exception:
        return None


async def arxiv_search(q: str) -> Optional[dict]:
    if not HTTPX:
        return None
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(
                "https://export.arxiv.org/api/query",
                params={"search_query": f"all:{q[:80]}", "start": 0, "max_results": 1},
            )
            xml = r.text
            titles = re.findall(r"<title>([^<]+)</title>", xml)
            paper = titles[1] if len(titles) > 1 else None
            ids = re.findall(r"<id>(https://arxiv.org/abs/[^<]+)</id>", xml)
            if not paper:
                return None
            return {"text": f"arXiv: {paper}", "source": "arXiv", "url": ids[0] if ids else ""}
    except Exception:
        return None


@app.get("/")
async def root():
    return {
        "service": "Milana-backend (AKSI)",
        "version": VERSION,
        "status": "running",
        "identity": {
            "did": "did:aksi:ed25519:sovereign-2026",
            "seed": "AKSI_DIMAX_v3_2026",
            "contact": "aksilove@internet.ru",
        },
        "modules": {
            "phase1_identity_auth": PHASE1_AVAILABLE,
            "chat_stream": CHAT_AVAILABLE,
            "admin": ADMIN_AVAILABLE,
            "identity": IDENTITY_AVAILABLE,
            "aksi_v2": AKSI_V2_AVAILABLE,
            "world_search": True,
            "codex": True,
            "llm_memory_resonance": True,
        },
        "try": [
            "GET /health",
            "GET /api/identity",
            "GET /api/codex",
            "POST /api/world/search",
            "POST /api/chat",
            "POST /api/aksi/chat",
            "/admin-ui/",
            "/docs",
        ],
        "frontend": "https://milana808.github.io/aksi/",
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "milana-backend",
        "version": VERSION,
        "chat": CHAT_AVAILABLE,
        "admin": ADMIN_AVAILABLE,
        "identity": IDENTITY_AVAILABLE,
        "httpx": HTTPX,
    }


@app.get("/version")
async def version():
    return {
        "version": VERSION,
        "api": "aksi-backend",
        "author": "Alfiia Bashirova (AKSI Project)",
    }


@app.get("/api/codex")
async def get_codex():
    return CODEX


@app.post("/api/codex/check")
async def check_codex(body: CodexCheckRequest):
    return codex_check(body.text)


@app.post("/api/world/search")
async def world_search(body: WorldSearchRequest):
    gate = codex_check(body.q)
    if not gate["ok"]:
        return {"ok": False, "refusal": gate, "results": []}

    results = []
    w = await wiki_search(body.q)
    if w:
        results.append(w)
    need_science = body.include_arxiv or bool(
        re.search(r"квант|физик|neural|algorithm|theorem|arxiv|науч", body.q, re.I)
    )
    if need_science:
        a = await arxiv_search(body.q)
        if a:
            results.append(a)

    text = "\n\n".join(r["text"] for r in results) if results else None
    sources = [f"{r['source']}" + (f" {r['url']}" if r.get("url") else "") for r in results]
    return {
        "ok": True,
        "q": body.q,
        "text": text,
        "sources": sources,
        "results": results,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/api/world/search")
async def world_search_get(q: str = Query(..., min_length=1)):
    return await world_search(WorldSearchRequest(q=q))


@app.post("/echo")
async def echo(request: EchoRequest):
    return {
        "echo": request.message,
        "timestamp": datetime.utcnow().isoformat(),
        "length": len(request.message),
    }


@app.get("/aksi/metrics")
async def get_metrics():
    return {
        **aksi_metrics,
        "ai_code_work": {
            **ai_code_metrics,
            "languages": dict(ai_code_metrics["languages"]),
            "operations": dict(ai_code_metrics["operations"]),
            "total_crypto_keys": len(crypto_keys_storage),
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/aksi/proof")
async def get_proof():
    return {
        "proof": {"eqs": aksi_metrics["eqs"], "model": "Ψ(AKSI)", "verified": True},
        "timestamp": datetime.utcnow().isoformat(),
        "signature": f"AKSI-proof-v{VERSION}",
    }


@app.post("/aksi/proof/stable")
async def create_stable_proof(request: ProofStableRequest):
    entry = {
        "signature": request.signature,
        "timestamp": request.timestamp or datetime.utcnow().isoformat(),
        "metrics": request.metrics or aksi_metrics,
        "stable": True,
    }
    proof_storage.append(entry)
    return {"status": "proof_recorded", "entry": entry}


@app.get("/aksi/logs")
async def get_logs(limit: int = 50, level: Optional[str] = None):
    filtered = logs_storage
    if level:
        filtered = [l for l in logs_storage if l.get("level") == level]
    return {"logs": filtered[-limit:], "total": len(filtered)}


@app.post("/aksi/logs/append")
async def append_log(request: LogAppendRequest):
    entry = {
        "level": request.level,
        "message": request.message,
        "context": request.context or {},
        "timestamp": datetime.utcnow().isoformat(),
    }
    logs_storage.append(entry)
    return {"status": "log_appended", "entry": entry}


@app.get("/aksi/logs/export")
async def export_logs(format: str = "json"):
    if format == "txt":
        text = "\n".join(
            f"[{l['timestamp']}] [{l['level']}] {l['message']}" for l in logs_storage
        )
        return PlainTextResponse(content=text)
    return JSONResponse(
        {"logs": logs_storage, "exported_at": datetime.utcnow().isoformat()}
    )


@app.post("/aksi/ai-work/session")
async def record_ai_work_session(request: AIWorkSessionRequest):
    if request.action == "start":
        sid = request.session_id or secrets.token_hex(16)
        ai_work_sessions.append(
            {
                "session_id": sid,
                "status": "active",
                "started_at": datetime.utcnow().isoformat(),
            }
        )
        ai_code_metrics["total_sessions"] += 1
        return {"status": "session_started", "session_id": sid}
    return {"status": "ok"}


@app.get("/aksi/ai-work/sessions")
async def get_ai_work_sessions(limit: int = 50):
    return {"sessions": ai_work_sessions[-limit:]}


@app.post("/aksi/crypto/record-key")
async def record_crypto_key(request: CryptoKeyRecordRequest):
    key_hash = hashlib.sha256(request.public_key.encode()).hexdigest()
    rec = {
        "key_id": secrets.token_hex(8),
        "key_hash": key_hash,
        "key_type": request.key_type,
        "created_at": datetime.utcnow().isoformat(),
    }
    crypto_keys_storage.append(rec)
    return {"status": "key_recorded", "key_id": rec["key_id"]}


@app.get("/aksi/crypto/keys")
async def get_crypto_keys(limit: int = 50):
    return {"keys": crypto_keys_storage[-limit:]}


@app.get("/aksi/crypto/keys/{key_id}")
async def get_crypto_key_detail(key_id: str):
    key = next((k for k in crypto_keys_storage if k.get("key_id") == key_id), None)
    if not key:
        raise HTTPException(404, "Key not found")
    return {"key": key}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
