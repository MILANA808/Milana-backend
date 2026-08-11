"""
Milana-backend (AKSI) - FastAPI backend для AKSI / Milana services

Copyright (c) 2025 Alfiia Bashirova (AKSI Project)
Contact: 716elektrik@mail.ru
All rights reserved.

AKSI Superintelligence System v0.3.0 — Phase1 identity + auth
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Dict, Any
import hashlib
import secrets
from collections import defaultdict

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

app = FastAPI(
    title="Milana-backend (AKSI)",
    description="FastAPI backend for AKSI Superintelligence System",
    version="0.3.0",
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

    @app.on_event("startup")
    async def _phase1_startup():
        if phase1_init_db:
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
    "eqs": 0.68,
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


@app.get("/")
async def root():
    response = {
        "service": "Milana-backend (AKSI)",
        "version": "0.3.0",
        "status": "running",
        "phase1": PHASE1_AVAILABLE,
        "description": "AKSI Superintelligence System",
        "phase1_endpoints": [
            "/api/identity",
            "/api/register",
            "/api/login",
            "/api/agents/handshake",
            "/api/reputation/status",
        ] if PHASE1_AVAILABLE else [],
        "documentation": {"swagger_ui": "/docs", "redoc": "/redoc"},
    }
    if AKSI_V2_AVAILABLE:
        response["aksi_v2"] = "active"
    return response


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "milana-backend",
        "phase1": PHASE1_AVAILABLE,
    }


@app.get("/version")
async def version():
    return {
        "version": "0.3.0",
        "api": "aksi-backend",
        "author": "Alfiia Bashirova (AKSI Project)",
        "contact": "716elektrik@mail.ru",
    }


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
            "avg_session_duration": (
                sum(ai_code_metrics["session_durations"]) / len(ai_code_metrics["session_durations"])
                if ai_code_metrics["session_durations"]
                else 0
            ),
            "total_crypto_keys": len(crypto_keys_storage),
            "active_sessions": len([s for s in ai_work_sessions if s.get("status") == "active"]),
        },
        "timestamp": datetime.utcnow().isoformat(),
        "uptime": "active",
    }


@app.get("/aksi/proof")
async def get_proof():
    return {
        "proof": {
            "eqs": aksi_metrics["eqs"],
            "empathy_advantage": f"+{int(aksi_metrics['empathy_boost'] * 100)}%",
            "grid_system": aksi_metrics["grid_system"],
            "model": "Ψ(AKSI)",
            "verified": True,
        },
        "timestamp": datetime.utcnow().isoformat(),
        "signature": "AKSI-proof-v0.1",
        "history": proof_storage[-10:] if proof_storage else [],
    }


@app.post("/aksi/proof/stable")
async def create_stable_proof(request: ProofStableRequest):
    proof_entry = {
        "signature": request.signature,
        "timestamp": request.timestamp or datetime.utcnow().isoformat(),
        "metrics": request.metrics or aksi_metrics,
        "stable": True,
    }
    proof_storage.append(proof_entry)
    return {"status": "proof_recorded", "entry": proof_entry, "total_proofs": len(proof_storage)}


@app.get("/aksi/logs")
async def get_logs(limit: int = 50, level: Optional[str] = None):
    filtered_logs = logs_storage
    if level:
        filtered_logs = [log for log in logs_storage if log.get("level") == level]
    return {"logs": filtered_logs[-limit:] if filtered_logs else [], "total": len(filtered_logs)}


@app.post("/aksi/logs/append")
async def append_log(request: LogAppendRequest):
    log_entry = {
        "level": request.level,
        "message": request.message,
        "context": request.context or {},
        "timestamp": datetime.utcnow().isoformat(),
    }
    logs_storage.append(log_entry)
    return {"status": "log_appended", "entry": log_entry}


@app.get("/aksi/logs/export")
async def export_logs(format: str = "json"):
    if format == "json":
        return JSONResponse(
            content={
                "logs": logs_storage,
                "exported_at": datetime.utcnow().isoformat(),
                "total": len(logs_storage),
            }
        )
    if format == "txt":
        text_logs = "\n".join(
            f"[{log['timestamp']}] [{log['level']}] {log['message']}" for log in logs_storage
        )
        return PlainTextResponse(content=text_logs)
    raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")


@app.post("/aksi/ai-work/session")
async def record_ai_work_session(request: AIWorkSessionRequest):
    if request.action == "start":
        session_id = request.session_id or secrets.token_hex(16)
        session = {
            "session_id": session_id,
            "status": "active",
            "started_at": datetime.utcnow().isoformat(),
            "files_modified": [],
            "total_lines_changed": 0,
            "languages": set(),
            "operations": [],
            "commits": [],
            "metadata": request.metadata or {},
        }
        ai_work_sessions.append(session)
        ai_code_metrics["total_sessions"] += 1
        return {"status": "session_started", "session_id": session_id}
    return {"status": "ok"}


@app.get("/aksi/ai-work/sessions")
async def get_ai_work_sessions(limit: int = 50, status: Optional[str] = None):
    filtered = ai_work_sessions
    if status:
        filtered = [s for s in ai_work_sessions if s.get("status") == status]
    out = []
    for session in filtered[-limit:]:
        sc = session.copy()
        if isinstance(sc.get("languages"), set):
            sc["languages"] = list(sc["languages"])
        out.append(sc)
    return {"sessions": out, "total": len(filtered)}


@app.post("/aksi/crypto/record-key")
async def record_crypto_key(request: CryptoKeyRecordRequest):
    key_hash = hashlib.sha256(request.public_key.encode()).hexdigest()
    key_record = {
        "key_id": secrets.token_hex(8),
        "key_hash": key_hash,
        "key_type": request.key_type,
        "public_key": request.public_key,
        "purpose": request.purpose,
        "algorithm": request.algorithm,
        "created_by": request.created_by,
        "created_at": datetime.utcnow().isoformat(),
        "metadata": request.metadata or {},
        "status": "active",
    }
    crypto_keys_storage.append(key_record)
    return {"status": "key_recorded", "key_id": key_record["key_id"], "key_hash": key_hash}


@app.get("/aksi/crypto/keys")
async def get_crypto_keys(limit: int = 50, key_type: Optional[str] = None, purpose: Optional[str] = None):
    filtered = crypto_keys_storage
    if key_type:
        filtered = [k for k in filtered if k.get("key_type") == key_type]
    if purpose:
        filtered = [k for k in filtered if k.get("purpose") == purpose]
    keys_summary = [
        {
            "key_id": k["key_id"],
            "key_hash": k["key_hash"],
            "key_type": k["key_type"],
            "purpose": k["purpose"],
            "algorithm": k["algorithm"],
            "created_by": k["created_by"],
            "created_at": k["created_at"],
            "status": k["status"],
        }
        for k in filtered[-limit:]
    ]
    return {"keys": keys_summary, "total": len(filtered)}


@app.get("/aksi/crypto/keys/{key_id}")
async def get_crypto_key_detail(key_id: str):
    key = next((k for k in crypto_keys_storage if k["key_id"] == key_id), None)
    if not key:
        raise HTTPException(status_code=404, detail="Key not found")
    return {"key": key}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
