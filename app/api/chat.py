"""SSE / plain chat with АКСИ — LLM + transparent offline fallback."""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator

router = APIRouter(tags=["chat"])


class ChatBody(BaseModel):
    message: Optional[str] = Field(default=None, max_length=12000)
    content: Optional[str] = Field(default=None, max_length=12000)
    mode: str = Field(default="aksi", max_length=40)
    history: List[Dict[str, Any]] = Field(default_factory=list, max_length=30)
    memory: str = Field(default="", max_length=8000)
    session_id: str = Field(default="default", min_length=1, max_length=128)

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, value: str) -> str:
        value = value.strip()
        if not value or not re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", value):
            raise ValueError("session_id may contain only letters, digits, _, ., :, and -")
        return value

    @field_validator("message", "content")
    @classmethod
    def normalize_text(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if value is not None else None


def _message(body: ChatBody) -> str:
    return (body.message or body.content or "").strip()


async def _stream_chunks(message: str, mode: str, history, memory: str, session_id: str):
    # Fall back only when the gateway module cannot be imported. Runtime errors must
    # not silently switch engines after a partial answer has already been sent.
    try:
        from app.core.llm import generate
    except ImportError:
        from app.core.aksi_engine import aksi_stream
        async for chunk in aksi_stream(message, mode, history, memory):
            yield chunk
        return

    async for chunk in generate(message, session_id=session_id, history=history, memory_text=memory):
        yield chunk


def _sse_response(body: ChatBody) -> StreamingResponse:
    message = _message(body)
    async def gen():
        full = []
        async for chunk in _stream_chunks(message, body.mode, body.history, body.memory, body.session_id):
            full.append(chunk)
            yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\\n\\n"
        answer = "".join(full)
        try:
            from app.core.crypto import get_crypto
            crypto = get_crypto()
            done = {"done": True, "signature": crypto.sign_message(answer + message)[:48], "did": crypto.get_did()}
        except Exception:
            from app.core.resonance import DID, sign_short
            done = {"done": True, "signature": sign_short(answer), "did": DID}
        yield f"data: {json.dumps(done, ensure_ascii=False)}\\n\\n"
    return StreamingResponse(gen(), media_type="text/event-stream")


@router.post("/api/chat/stream")
@router.post("/api/aksi/chat")
@router.post("/chat/stream")
async def chat_stream(body: ChatBody):
    if not _message(body):
        raise HTTPException(status_code=422, detail="message required")
    return _sse_response(body)


@router.post("/api/chat")
async def chat_once(body: ChatBody):
    message = _message(body)
    if not message:
        raise HTTPException(status_code=422, detail="message required")
    chunks = []
    async for chunk in _stream_chunks(message, body.mode, body.history, body.memory, body.session_id):
        chunks.append(chunk)
    answer = "".join(chunks)
    try:
        from app.core.crypto import get_crypto
        crypto = get_crypto()
        return {"answer": answer, "did": crypto.get_did(), "signature": crypto.sign_message(answer)[:48]}
    except Exception:
        from app.core.resonance import DID, sign_short
        return {"answer": answer, "did": DID, "signature": sign_short(answer)}
