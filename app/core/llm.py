"""AKSI LLM — xAI / OpenAI / Ollama via env + offline + Resonance

Secrets only from environment (.env). Never hardcode API keys.
Priority: XAI_API_KEY → OPENAI_API_KEY → Ollama → offline knowledge.
"""
from __future__ import annotations

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
XAI_API_KEY = os.getenv("XAI_API_KEY", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
XAI_MODEL = os.getenv("XAI_MODEL", "grok-3")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

SYSTEM = (
    "Ты — АКСИ, суверенный ИИ. Проект АКСИ. "
    "Отвечай по-русски, по существу, честно. Не выдумывай факты. "
    "Не называй себя ChatGPT, Claude, Gemini или Grok от лица АКСИ."
)


def _messages(message: str, hist: List[dict], ctx: str) -> List[dict]:
    msgs = [{"role": "system", "content": SYSTEM}]
    if ctx:
        msgs.append({"role": "system", "content": "Контекст диалога:\n" + ctx[:4000]})
    for m in hist[-10:]:
        role = "user" if m.get("role") == "user" else "assistant"
        content = (m.get("content") or "")[:2000]
        if content:
            msgs.append({"role": role, "content": content})
    msgs.append({"role": "user", "content": message})
    return msgs


async def _chat_openai_compatible(
    base_url: str,
    api_key: str,
    model: str,
    messages: List[dict],
) -> str:
    if httpx is None or not api_key:
        return ""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(
                f"{base_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": 0.7,
                    "stream": False,
                },
            )
            if r.status_code != 200:
                return ""
            data = r.json()
            choices = data.get("choices") or []
            if not choices:
                return ""
            return (choices[0].get("message") or {}).get("content") or ""
    except Exception:
        return ""


async def _ollama(message: str, hist: List[dict], ctx: str) -> str:
    if httpx is None:
        return ""
    parts = [SYSTEM]
    if ctx:
        parts.append("Контекст:\n" + ctx)
    for m in hist[-8:]:
        role = "User" if m.get("role") == "user" else "АКСИ"
        parts.append(f"{role}: {m.get('content', '')}")
    parts.append(f"User: {message}\nАКСИ:")
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            r = await client.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": "\n".join(parts),
                    "stream": False,
                },
            )
            if r.status_code != 200:
                return ""
            return (r.json() or {}).get("response") or ""
    except Exception:
        return ""


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

    hit = knowledge.lookup(message)
    if hit:
        out = f"{hit}\n\n🔏 {sign_short(hit)}"
        memory.append(session_id, "assistant", hit)
        yield out
        return

    hist = history or memory.history(session_id, 16)
    ctx = memory.context_text(session_id, 12)
    msgs = _messages(message, hist, ctx)
    raw = ""

    if XAI_API_KEY:
        raw = await _chat_openai_compatible(
            "https://api.x.ai/v1", XAI_API_KEY, XAI_MODEL, msgs
        )
    if not raw and OPENAI_API_KEY:
        raw = await _chat_openai_compatible(
            "https://api.openai.com/v1", OPENAI_API_KEY, OPENAI_MODEL, msgs
        )
    if not raw:
        raw = await _ollama(message, hist, ctx)

    if raw:
        memory.append(session_id, "assistant", raw)
        yield raw + f"\n\n🔏 {sign_short(raw)}"
        return

    idb = identity_block()
    fallback = (
        f"Слышу: «{message[:120]}». Внешняя модель недоступна — ядро АКСИ. "
        f"DID: {idb.get('did')}. Укажите XAI_API_KEY или OPENAI_API_KEY в .env "
        f"либо запустите Ollama ({OLLAMA_MODEL})."
    )
    memory.append(session_id, "assistant", fallback)
    yield fallback + f"\n\n🔏 {sign_short(fallback)}"
