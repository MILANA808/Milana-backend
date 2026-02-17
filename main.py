"""
Milana-backend (AKSI) - FastAPI backend для AKSI / Milana services

Copyright (c) 2025 Alfiia Bashirova (AKSI Project)
Contact: 716elektrik@mail.ru
All rights reserved.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Dict, Any
import json
import os
import hashlib
import secrets
from collections import defaultdict

app = FastAPI(
    title="Milana-backend (AKSI)",
    description="FastAPI backend for AKSI / Milana services",
    version="0.1.0"
)

# Настройка CORS для интеграции с фронтендом
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене следует указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Хранилище для логов (в продакшене следует использовать БД)
logs_storage: List[dict] = []

# Хранилище для proof записей
proof_storage: List[dict] = []

# Хранилище для сессий работы AI
ai_work_sessions: List[dict] = []

# Хранилище криптографических ключей и подписей
crypto_keys_storage: List[dict] = []

# Детальные метрики работы AI над кодом
ai_code_metrics = {
    "total_sessions": 0,
    "total_code_changes": 0,
    "total_lines_modified": 0,
    "total_files_touched": 0,
    "total_commits": 0,
    "languages": defaultdict(int),
    "operations": defaultdict(int),  # create, update, delete, refactor
    "session_durations": [],
    "error_rate": 0.0,
    "success_rate": 100.0
}

# Метрики AKSI
aksi_metrics = {
    "eqs": 0.68,  # Emotional Quality Score
    "empathy_boost": 0.25,  # 25% выше чем стандартные LLM
    "grid_system": "3x3",
    "status": "active",
    "ai_code_work": ai_code_metrics
}


class EchoRequest(BaseModel):
    """Модель для POST /echo"""
    message: str


class ProofStableRequest(BaseModel):
    """Модель для POST /aksi/proof/stable"""
    signature: str
    timestamp: Optional[str] = None
    metrics: Optional[dict] = None


class LogAppendRequest(BaseModel):
    """Модель для POST /aksi/logs/append"""
    level: str
    message: str
    context: Optional[dict] = None


class AIWorkSessionRequest(BaseModel):
    """Модель для POST /aksi/ai-work/session"""
    session_id: Optional[str] = None
    action: str  # start, update, end
    files_modified: Optional[List[str]] = None
    lines_changed: Optional[int] = None
    language: Optional[str] = None
    operation: Optional[str] = None  # create, update, delete, refactor
    commit_hash: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class CryptoKeyRecordRequest(BaseModel):
    """Модель для POST /aksi/crypto/record-key"""
    key_type: str  # ed25519, rsa, ecdsa
    public_key: str
    purpose: str  # signing, verification, encryption
    algorithm: str
    created_by: str  # AI или user identifier
    metadata: Optional[Dict[str, Any]] = None


@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "service": "Milana-backend (AKSI)",
        "version": "0.2.0",
        "status": "running",
        "description": "FastAPI backend with AI work tracking and cryptographic key management",
        "endpoints": {
            "health_monitoring": [
                "/health",
                "/version",
                "/echo"
            ],
            "aksi_core": [
                "/aksi/metrics",
                "/aksi/proof",
                "/aksi/proof/stable",
                "/aksi/logs",
                "/aksi/logs/append",
                "/aksi/logs/export"
            ],
            "ai_work_tracking": [
                "/aksi/ai-work/session (POST)",
                "/aksi/ai-work/sessions (GET)"
            ],
            "crypto_management": [
                "/aksi/crypto/record-key (POST)",
                "/aksi/crypto/keys (GET)",
                "/aksi/crypto/keys/{key_id} (GET)"
            ]
        },
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc"
        }
    }


@app.get("/health")
async def health():
    """Проверка здоровья сервиса"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "milana-backend"
    }


@app.get("/version")
async def version():
    """Версия API"""
    return {
        "version": "0.1.0",
        "api": "aksi-backend",
        "author": "Alfiia Bashirova (AKSI Project)",
        "contact": "716elektrik@mail.ru"
    }


@app.post("/echo")
async def echo(request: EchoRequest):
    """Эхо-эндпоинт для тестирования"""
    return {
        "echo": request.message,
        "timestamp": datetime.utcnow().isoformat(),
        "length": len(request.message)
    }


@app.get("/aksi/metrics")
async def get_metrics():
    """Получить метрики AKSI с детальными данными о работе AI"""
    # Конвертируем defaultdict в обычные dict для JSON
    metrics_snapshot = {
        **aksi_metrics,
        "ai_code_work": {
            **ai_code_metrics,
            "languages": dict(ai_code_metrics["languages"]),
            "operations": dict(ai_code_metrics["operations"]),
            "avg_session_duration": sum(ai_code_metrics["session_durations"]) / len(ai_code_metrics["session_durations"]) if ai_code_metrics["session_durations"] else 0,
            "total_crypto_keys": len(crypto_keys_storage),
            "active_sessions": len([s for s in ai_work_sessions if s.get("status") == "active"])
        },
        "timestamp": datetime.utcnow().isoformat(),
        "uptime": "active"
    }
    return metrics_snapshot


@app.get("/aksi/proof")
async def get_proof():
    """Получить доказательство сознательного цикла AKSI"""
    return {
        "proof": {
            "eqs": aksi_metrics["eqs"],
            "empathy_advantage": f"+{int(aksi_metrics['empathy_boost'] * 100)}%",
            "grid_system": aksi_metrics["grid_system"],
            "model": "Ψ(AKSI)",
            "verified": True
        },
        "timestamp": datetime.utcnow().isoformat(),
        "signature": "AKSI-proof-v0.1",
        "history": proof_storage[-10:] if proof_storage else []
    }


@app.post("/aksi/proof/stable")
async def create_stable_proof(request: ProofStableRequest):
    """Создать стабильную запись proof с подписью"""
    proof_entry = {
        "signature": request.signature,
        "timestamp": request.timestamp or datetime.utcnow().isoformat(),
        "metrics": request.metrics or aksi_metrics,
        "stable": True
    }
    proof_storage.append(proof_entry)

    return {
        "status": "proof_recorded",
        "entry": proof_entry,
        "total_proofs": len(proof_storage)
    }


@app.get("/aksi/logs")
async def get_logs(limit: int = 50, level: Optional[str] = None):
    """Получить логи AKSI"""
    filtered_logs = logs_storage

    if level:
        filtered_logs = [log for log in logs_storage if log.get("level") == level]

    # Возвращаем последние N логов
    return {
        "logs": filtered_logs[-limit:] if filtered_logs else [],
        "total": len(filtered_logs),
        "limit": limit,
        "filter": {"level": level} if level else None
    }


@app.post("/aksi/logs/append")
async def append_log(request: LogAppendRequest):
    """Добавить запись в лог"""
    log_entry = {
        "level": request.level,
        "message": request.message,
        "context": request.context or {},
        "timestamp": datetime.utcnow().isoformat()
    }
    logs_storage.append(log_entry)

    return {
        "status": "log_appended",
        "entry": log_entry,
        "total_logs": len(logs_storage)
    }


@app.get("/aksi/logs/export")
async def export_logs(format: str = "json"):
    """Экспорт всех логов"""
    if format == "json":
        return JSONResponse(content={
            "logs": logs_storage,
            "exported_at": datetime.utcnow().isoformat(),
            "total": len(logs_storage)
        })
    elif format == "txt":
        text_logs = "\n".join([
            f"[{log['timestamp']}] [{log['level']}] {log['message']}"
            for log in logs_storage
        ])
        return PlainTextResponse(content=text_logs)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")


@app.post("/aksi/ai-work/session")
async def record_ai_work_session(request: AIWorkSessionRequest):
    """Записать сессию работы AI над кодом"""

    if request.action == "start":
        # Создаём новую сессию
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
            "metadata": request.metadata or {}
        }
        ai_work_sessions.append(session)
        ai_code_metrics["total_sessions"] += 1

        return {
            "status": "session_started",
            "session_id": session_id,
            "started_at": session["started_at"]
        }

    elif request.action == "update":
        # Обновляем существующую сессию
        session = next((s for s in ai_work_sessions if s["session_id"] == request.session_id), None)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        if request.files_modified:
            session["files_modified"].extend(request.files_modified)
            ai_code_metrics["total_files_touched"] += len(request.files_modified)
            ai_code_metrics["total_code_changes"] += 1

        if request.lines_changed:
            session["total_lines_changed"] += request.lines_changed
            ai_code_metrics["total_lines_modified"] += request.lines_changed

        if request.language:
            session["languages"].add(request.language)
            ai_code_metrics["languages"][request.language] += 1

        if request.operation:
            session["operations"].append(request.operation)
            ai_code_metrics["operations"][request.operation] += 1

        if request.commit_hash:
            session["commits"].append(request.commit_hash)
            ai_code_metrics["total_commits"] += 1

        session["last_updated"] = datetime.utcnow().isoformat()

        return {
            "status": "session_updated",
            "session_id": session["session_id"],
            "total_changes": len(session["operations"])
        }

    elif request.action == "end":
        # Завершаем сессию
        session = next((s for s in ai_work_sessions if s["session_id"] == request.session_id), None)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        session["status"] = "completed"
        session["ended_at"] = datetime.utcnow().isoformat()

        # Вычисляем длительность сессии
        started = datetime.fromisoformat(session["started_at"])
        ended = datetime.fromisoformat(session["ended_at"])
        duration_seconds = (ended - started).total_seconds()
        session["duration_seconds"] = duration_seconds
        ai_code_metrics["session_durations"].append(duration_seconds)

        return {
            "status": "session_ended",
            "session_id": session["session_id"],
            "duration_seconds": duration_seconds,
            "summary": {
                "files_modified": len(set(session["files_modified"])),
                "lines_changed": session["total_lines_changed"],
                "languages": list(session["languages"]),
                "operations": session["operations"],
                "commits": len(session["commits"])
            }
        }

    else:
        raise HTTPException(status_code=400, detail=f"Invalid action: {request.action}")


@app.get("/aksi/ai-work/sessions")
async def get_ai_work_sessions(limit: int = 50, status: Optional[str] = None):
    """Получить список сессий работы AI"""
    filtered_sessions = ai_work_sessions

    if status:
        filtered_sessions = [s for s in ai_work_sessions if s.get("status") == status]

    # Конвертируем set в list для JSON сериализации
    sessions_json = []
    for session in filtered_sessions[-limit:]:
        session_copy = session.copy()
        if "languages" in session_copy and isinstance(session_copy["languages"], set):
            session_copy["languages"] = list(session_copy["languages"])
        sessions_json.append(session_copy)

    return {
        "sessions": sessions_json,
        "total": len(filtered_sessions),
        "limit": limit,
        "filter": {"status": status} if status else None
    }


@app.post("/aksi/crypto/record-key")
async def record_crypto_key(request: CryptoKeyRecordRequest):
    """Записать криптографический ключ, созданный при работе AI"""

    # Генерируем хэш публичного ключа для идентификации
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
        "status": "active"
    }

    crypto_keys_storage.append(key_record)

    # Логируем создание ключа
    log_entry = {
        "level": "info",
        "message": f"Cryptographic key recorded: {request.key_type} for {request.purpose}",
        "context": {
            "key_id": key_record["key_id"],
            "key_hash": key_hash,
            "created_by": request.created_by
        },
        "timestamp": datetime.utcnow().isoformat()
    }
    logs_storage.append(log_entry)

    return {
        "status": "key_recorded",
        "key_id": key_record["key_id"],
        "key_hash": key_hash,
        "created_at": key_record["created_at"]
    }


@app.get("/aksi/crypto/keys")
async def get_crypto_keys(limit: int = 50, key_type: Optional[str] = None, purpose: Optional[str] = None):
    """Получить список записанных криптографических ключей"""
    filtered_keys = crypto_keys_storage

    if key_type:
        filtered_keys = [k for k in filtered_keys if k.get("key_type") == key_type]

    if purpose:
        filtered_keys = [k for k in filtered_keys if k.get("purpose") == purpose]

    # Не возвращаем полные публичные ключи в списке (только по запросу конкретного ключа)
    keys_summary = []
    for key in filtered_keys[-limit:]:
        keys_summary.append({
            "key_id": key["key_id"],
            "key_hash": key["key_hash"],
            "key_type": key["key_type"],
            "purpose": key["purpose"],
            "algorithm": key["algorithm"],
            "created_by": key["created_by"],
            "created_at": key["created_at"],
            "status": key["status"]
        })

    return {
        "keys": keys_summary,
        "total": len(filtered_keys),
        "limit": limit,
        "filters": {
            "key_type": key_type,
            "purpose": purpose
        }
    }


@app.get("/aksi/crypto/keys/{key_id}")
async def get_crypto_key_detail(key_id: str):
    """Получить полную информацию о криптографическом ключе"""
    key = next((k for k in crypto_keys_storage if k["key_id"] == key_id), None)

    if not key:
        raise HTTPException(status_code=404, detail="Key not found")

    return {
        "key": key,
        "retrieved_at": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
