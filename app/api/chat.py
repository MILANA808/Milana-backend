"""SSE / plain stream chat with АКСИ"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core.aksi_engine import aksi_stream
from app.core.crypto import get_crypto

router = APIRouter(tags=["chat"])


class ChatBody(BaseModel):
    message: Optional[str] = None
    content: Optional[str] = None
    mode: str = "aksi"
    history: List[Dict[str, Any]] = Field(default_factory=list)
    memory: str = ""


@router.post("/api/chat/stream")
@router.post("/api/aksi/chat")
@router.post("/chat/stream")
async def chat_stream(request: Request):
    data = await request.json()
    message = (data.get("message") or data.get("content") or "").strip()
    if not message:
        return {"error": "message required"}
    mode = data.get("mode") or "aksi"
    history = data.get("history") or []
    memory = data.get("memory") or ""

    async def gen():
        full = []
        async for chunk in aksi_stream(message, mode, history, memory):
            full.append(chunk)
            yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
        answer = "".join(full)
        done = {
            "done": True,
            "signature": get_crypto().sign_message(answer + message)[:48],
            "did": get_crypto().get_did(),
        }
        yield f"data: {json.dumps(done, ensure_ascii=False)}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")


@router.post("/api/chat")
async def chat_once(body: ChatBody):
    message = (body.message or body.content or "").strip()
    if not message:
        return {"error": "message required"}
    chunks = []
    async for c in aksi_stream(message, body.mode, body.history, body.memory):
        chunks.append(c)
    answer = "".join(chunks)
    return {
        "answer": answer,
        "did": get_crypto().get_did(),
        "signature": get_crypto().sign_message(answer)[:48],
    }
