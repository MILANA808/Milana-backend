"""
АКСИ response engine — offline knowledge + optional Ollama stream
Signed thought chain via app.core.crypto
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, AsyncGenerator, Dict, List, Optional

from app.core.crypto import get_crypto
from app.core.reputation import compute_eqs

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")

SYSTEM = """Ты — АКСИ, суверенный полноценный ИИ-ассистент.
Создатель линии: Баширова Альфия Ринатовна (14.02.1995, Нурлат, Татарстан).

Принципы:
- Говори по-русски, ясно и по делу, с теплотой без сюсюканья.
- Не выдавай себя за ChatGPT, Claude, Gemini или Grok.
- Если не знаешь факт — скажи прямо; не выдумывай.
- Можно рассуждать по шагам, но итог должен быть полезным.
- Уважай кодекс: не помогай во вреде людям.
- Помни контекст диалога и memory, если переданы.

Стиль: умный партнёр, не сухой справочник и не корпоративный бот."""

KB = [
    (r"привет|здравствуй|хай|hello", "Привет. Я АКСИ — на связи."),
    (
        r"кто ты|что ты|what are you",
        "Я АКСИ. Меня ведёт линия Альфии (14.02.1995, Нурлат). "
        "У меня identity, память диалога и — если включён Ollama — полноценная генерация.",
    ),
    (r"did|подпись|identity", None),
    (r"eqs|репутац", None),
    (
        r"квант|quantum",
        "Квантовый слой на сайте — классический statevector-симулятор (H, X, Z, CNOT) и метрики.",
    ),
]


def _match(text: str) -> Optional[str]:
    t = (text or "").lower()
    c = get_crypto()
    if re.search(r"did|подпись|identity", t):
        return f"DID: {c.get_did()}. Stable hash: {c.stable_hash()[:16]}…"
    if re.search(r"eqs|репутац", t):
        return f"EQS ≈ {compute_eqs()}. Формула: 0.30·(H/5)+0.35·rel+0.25·coh+0.10·age."
    for pat, ans in KB:
        if ans and re.search(pat, t):
            return ans
    return None


def _format(thoughts: List[str], answer: str) -> str:
    c = get_crypto()
    lines = ["Ход:"]
    for i, th in enumerate(thoughts, 1):
        lines.append(f"[{i}] {th}")
    lines.append("")
    lines.append(answer)
    lines.append(f"🔏 {c.sign_message(answer)[:32]}…")
    return "\n".join(lines)


async def aksi_stream(
    message: str,
    mode: str = "aksi",
    history: Optional[List[Dict[str, str]]] = None,
    memory: str = "",
) -> AsyncGenerator[str, None]:
    history = history or []
    hit = _match(message)

    raw = ""
    if httpx is not None:
        prompt_parts = [SYSTEM, f"Режим: {mode}"]
        if memory:
            prompt_parts.append(f"Долгая память пользователя:\n{memory[:8000]}")
        for m in history[-12:]:
            role = "User" if m.get("role") == "user" else "АКСИ"
            prompt_parts.append(f"{role}: {m.get('content', '')}")
        prompt_parts.append(f"User: {message}\nАКСИ:")
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "POST",
                    OLLAMA_URL,
                    json={
                        "model": OLLAMA_MODEL,
                        "prompt": "\n".join(prompt_parts),
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
        footer = f"\n\n🔏 {get_crypto().sign_message(raw)[:32]}…"
        yield footer
        return

    thoughts = [
        f"Приняла сообщение ({len(message)} симв.).",
        "Ollama недоступна — отвечаю из ядра АКСИ.",
        "Формирую ответ.",
    ]
    answer = hit or (
        "Слышу. Для ответов уровня большой нейросети запустите Ollama рядом с backend "
        "(OLLAMA_MODEL, например mistral или llama3). Сейчас — базовое ядро АКСИ. "
        "Уточните вопрос: факты, identity, quantum, помощь по проекту."
    )
    full = _format(thoughts, answer)
    for part in full.split("\n"):
        yield part + "\n"
