"""SSE / plain chat with АКСИ — llm + aksi_engine fallback"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

router = APIRouter(tags=["chat"])


class ChatBody(BaseModel):
    message: Optional[str] = None
    content: Optional[str] = None
    mode: str = "aksi"
    history: List[Dict[str, Any]] = Field(default_factory=list)
    memory: str = ""
    session_id: str = "default"


async def _stream_chunks(message: str, mode: str, history, memory: str, session_id: str):
    # prefer new core.llm
    try:
        from app.core.llm import generate

        async for chunk in generate(message, session_id=session_id, history=history):
            yield chunk
        return
    except Exception:
        pass
    # fallback aksi_engine
    from app.core.aksi_engine import aksi_stream

    async for chunk in aksi_stream(message, mode, history, memory):
        yield chunk


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
    session_id = data.get("session_id") or "default"

    async def gen():
        full = []
        async for chunk in _stream_chunks(message, mode, history, memory, session_id):
            full.append(chunk)
            yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
        answer = "".join(full)
        try:
            from app.core.crypto import get_crypto

            done = {
                "done": True,
                "signature": get_crypto().sign_message(answer + message)[:48],
                "did": get_crypto().get_did(),
            }
        except Exception:
            from app.core.resonance import DID, sign_short

            done = {"done": True, "signature": sign_short(answer), "did": DID}
        yield f"data: {json.dumps(done, ensure_ascii=False)}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")


@router.post("/api/chat")
async def chat_once(body: ChatBody):
    message = (body.message or body.content or "").strip()
    if not message:
        return {"error": "message required"}
    chunks = []
    async for c in _stream_chunks(
        message, body.mode, body.history, body.memory, body.session_id
    ):
        chunks.append(c)
    answer = "".join(chunks)
    try:
        from app.core.crypto import get_crypto

        return {
            "answer": answer,
            "did": get_crypto().get_did(),
            "signature": get_crypto().sign_message(answer)[:48],
        }
    except Exception:
        from app.core.resonance import DID, sign_short

        return {"answer": answer, "did": DID, "signature": sign_short(answer)}
