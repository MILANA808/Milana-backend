"""AKSI LLM — Ollama stream + offline knowledge + Resonance signature"""
from __future__ import annotations

import json
import os
from typing import AsyncGenerator, List, Optional

from app.core import knowledge, memory
from app.core.resonance import identity_block, sign_short

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")

SYSTEM = """Ты — АКСИ, суверенный ИИ. Создатель: Альфия (14.02.1995).
Отвечай по-русски, по существу. Не выдумывай факты. Не называй себя ChatGPT."""


async def generate(
    message: str,
    session_id: str = "default",
    history: Optional[List[dict]] = None,
) -> AsyncGenerator[str, None]:
    message = (message or "").strip()
    if not message:
        yield "Пустое сообщение."
        return

    memory.append(session_id, "user", message)

    # offline hit
    hit = knowledge.lookup(message)
    if hit:
        sig = sign_short(hit)
        out = f"{hit}\n\n🔏 {sig}"
        memory.append(session_id, "assistant", hit)
        yield out
        return

    hist = history or memory.history(session_id, 16)
    raw = ""

    if httpx is not None:
        parts = [SYSTEM]
        ctx = memory.context_text(session_id, 12)
        if ctx:
            parts.append("Контекст:\n" + ctx)
        for m in hist[-8:]:
            role = "User" if m.get("role") == "user" else "АКСИ"
            parts.append(f"{role}: {m.get('content', '')}")
        parts.append(f"User: {message}\nАКСИ:")
        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                async with client.stream(
                    "POST",
                    OLLAMA_URL,
                    json={
                        "model": OLLAMA_MODEL,
                        "prompt": "\n".join(parts),
                        "stream": True,
                    },
                ) as resp:
                    if resp.status_code == 200:
                        async for line in resp.aiter_lines():
                            if not line:
                                continue
                            try:
                                data = json.loads(line)
                            except json.JSONDecodeError:
                                continue
                            chunk = data.get("response") or ""
                            if chunk:
                                raw += chunk
                                yield chunk
                            if data.get("done"):
                                break
        except Exception:
            raw = ""

    if raw:
        memory.append(session_id, "assistant", raw)
        yield f"\n\n🔏 {sign_short(raw)}"
        return

    # final offline
    idb = identity_block()
    fallback = (
        f"Слышу: «{message[:120]}». Ollama сейчас недоступна — отвечаю из ядра АКСИ. "
        f"DID: {idb['did']}. Запустите ollama serve и модель {OLLAMA_MODEL}."
    )
    memory.append(session_id, "assistant", fallback)
    yield fallback + f"\n\n🔏 {sign_short(fallback)}"
