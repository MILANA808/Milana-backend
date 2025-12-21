from __future__ import annotations

import hashlib
import json
import os
import pathlib
import time
from collections import deque
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel


APP_VERSION = os.getenv("AKSI_VERSION", "0.1.0")
DEFAULT_ORIGINS = "https://milana808.github.io,http://localhost:3000,http://127.0.0.1:3000"
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("AKSI_CORS_ORIGINS", DEFAULT_ORIGINS).split(",")
    if origin.strip()
]
LOG_CAP = int(os.getenv("AKSI_LOG_CAP", "200"))
PROOF_PATH = pathlib.Path("PROOF_SHA256.txt")

# Безопасность/лимиты для EQS/Ψ
AKSI_DEMO = os.getenv("AKSI_DEMO", "1") == "1"
API_KEY = os.getenv("AKSI_API_KEY", "").strip()
RATE = int(os.getenv("AKSI_RATE_LIMIT", "10" if AKSI_DEMO else "120"))
_hits: List[float] = []


def _allow() -> bool:
    now = time.time()
    while _hits and now - _hits[0] > 60:
        _hits.pop(0)
    if len(_hits) >= RATE:
        return False
    _hits.append(now)
    return True


app = FastAPI(title="Milana Backend (AKSI)", version=APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_logs: deque[Dict[str, Any]] = deque(maxlen=LOG_CAP)


def _log(event: str, payload: Optional[Dict[str, Any]] = None) -> None:
    _logs.append(
        {
            "ts": int(time.time()),
            "event": event,
            "payload": payload or {},
        }
    )


class Echo(BaseModel):
    data: Dict[str, Any]


class EQSIn(BaseModel):
    text: str


class PsiIn(BaseModel):
    omega: float
    phi: float
    amplitude: float


@app.get("/")
def index() -> Dict[str, Any]:
    """Простой корневой маршрут для быстрой проверки живости сервиса."""
    summary = {
        "service": "AKSI Bot Backend",
        "version": APP_VERSION,
        "demo": AKSI_DEMO,
        "rate": RATE,
        "endpoints": [
            "/health",
            "/version",
            "/echo",
            "/eqs/score",
            "/psi/state",
            "/aksi/metrics",
            "/aksi/proof",
            "/aksi/proof/stable",
            "/aksi/logs",
            "/aksi/logs/append",
            "/aksi/logs/export",
        ],
    }
    _log("index", {"demo": AKSI_DEMO})
    return summary


@app.get("/health")
def health() -> Dict[str, Any]:
    _log("health")
    return {"status": "ok", "demo": AKSI_DEMO, "rate": RATE}


@app.get("/version")
def version() -> Dict[str, str]:
    _log("version", {"version": APP_VERSION})
    return {"version": APP_VERSION}


@app.post("/echo")
def echo(payload: Echo) -> Dict[str, Any]:
    data = payload.model_dump()
    _log("echo", data)
    return data


@app.post("/eqs/score")
def eqs_score(payload: EQSIn, x_api_key: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    if not AKSI_DEMO:
        if not API_KEY or x_api_key != API_KEY:
            raise HTTPException(status_code=401, detail="Missing/invalid X-API-Key")
    if not _allow():
        raise HTTPException(status_code=429, detail="Rate limited")

    text = payload.text.strip()
    words = text.lower().split()
    pos = sum(1 for w in words if w in {"любовь", "свет", "радость", "надежда"})
    neg = sum(1 for w in words if w in {"страх", "боль", "грусть", "злость"})
    score = max(0, min(100, 50 + (pos - neg) * 12))
    polarity = (pos - neg) / max(1, len(words))
    result = {"score": score, "polarity": polarity, "subjectivity": 0.5}
    _log("eqs_score", result | {"text_len": len(words)})
    return result


@app.post("/psi/state")
def psi_state(payload: PsiIn, x_api_key: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    if not AKSI_DEMO:
        if not API_KEY or x_api_key != API_KEY:
            raise HTTPException(status_code=401, detail="Missing/invalid X-API-Key")
    if not _allow():
        raise HTTPException(status_code=429, detail="Rate limited")

    psi = payload.amplitude
    result = {"psi": psi, "omega": payload.omega, "phi": payload.phi}
    _log("psi_state", result)
    return result


@app.get("/aksi/metrics")
def metrics() -> Dict[str, Any]:
    data = {
        "ok": True,
        "ts": int(time.time()),
        "version": APP_VERSION,
        "demo": AKSI_DEMO,
        "rate": RATE,
    }
    _log("metrics", data)
    return data


@app.get("/aksi/proof")
def proof_ephemeral() -> Dict[str, Any]:
    payload = f"AKSI-PROOF:{int(time.time())}".encode()
    digest = hashlib.sha256(payload).hexdigest()
    _log("proof_ephemeral", {"sha256": digest})
    return {"sha256": digest, "stable": False}


@app.post("/aksi/proof/stable")
def proof_stable() -> Dict[str, Any]:
    if PROOF_PATH.exists():
        digest = PROOF_PATH.read_text().strip()
        _log("proof_stable_read", {"sha256": digest})
        return {"sha256": digest, "stable": True}

    payload = f"AKSI-PROOF:seed:{int(time.time())}".encode()
    digest = hashlib.sha256(payload).hexdigest()
    PROOF_PATH.write_text(digest)
    _log("proof_stable_write", {"sha256": digest})
    return {"sha256": digest, "stable": True}


@app.get("/aksi/logs")
def logs_list(limit: int = 100) -> Dict[str, Any]:
    data = list(_logs)[-min(limit, LOG_CAP) :]
    return {"items": data, "count": len(data), "cap": LOG_CAP}


@app.post("/aksi/logs/append")
async def logs_append(req: Request) -> Dict[str, Any]:
    try:
        body = await req.json()
    except Exception:
        raw_body = await req.body()
        body = {"raw": raw_body.decode("utf-8", errors="replace")}

    _log("append", body if isinstance(body, dict) else {"raw": str(body)})
    return {"ok": True, "size": len(_logs)}


@app.get("/aksi/logs/export", response_class=PlainTextResponse)
def logs_export() -> PlainTextResponse:
    lines = [json.dumps(entry, ensure_ascii=False) for entry in _logs]
    content = "\n".join(lines)
    return PlainTextResponse(content, media_type="text/plain; charset=utf-8")
