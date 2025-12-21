from __future__ import annotations

import hashlib
import json
import os
import pathlib
import time
from collections import deque
from typing import Any, Dict, Optional

from fastapi import FastAPI, Request
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


@app.get("/health")
def health() -> Dict[str, Any]:
    _log("health")
    return {"status": "ok"}


@app.get("/version")
def version() -> Dict[str, str]:
    _log("version", {"version": APP_VERSION})
    return {"version": APP_VERSION}


@app.post("/echo")
def echo(payload: Echo) -> Dict[str, Any]:
    data = payload.model_dump()
    _log("echo", data)
    return data


@app.get("/aksi/metrics")
def metrics() -> Dict[str, Any]:
    data = {"ok": True, "ts": int(time.time()), "version": APP_VERSION}
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
