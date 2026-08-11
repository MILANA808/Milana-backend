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

SYSTEM = """Ты — АКСИ, суверенный ИИ. Создатель: Баширова Альфия Ринатовна (14.02.1995, Нурлат).
Говори по-русски. Сначала 2–3 строки «МЫСЛЬ: …», затем «ОТВЕТ: …».
Не называй себя ChatGPT."""

KB = [
    (r"привет|здравствуй|хай|hello", "Привет. Я АКСИ — на связи. Resonance активен."),
    (r"кто ты|что ты|what are you", "Я АКСИ. Меня создала Альфия 14.02.1995 в Нурлате. DID и подписи — моя идентичность."),
    (r"did|подпись|identity", None),  # filled dynamically
    (r"eqs|репутац", None),
    (r"квант|quantum", "Квантовый слой — классический statevector-симулятор (H, X, Z, CNOT) и метрики QCLI."),
    (r"github|агент", "GitHub-агент и манифесты — в roadmap Phase 2–3. Сейчас: identity + chat + admin."),
]


def _match(text: str) -> Optional[str]:
    t = (text or "").lower()
    c = get_crypto()
    if re.search(r"did|подпись|identity", t):
        return f"DID: {c.get_did()}. Stable hash: {c.stable_hash()[:16]}…"
    if re.search(r"eqs|репутац", t):
        return f"EQS сейчас ≈ {compute_eqs()}. Формула: 0.30·(H/5)+0.35·rel+0.25·coh+0.10·age."
    for pat, ans in KB:
        if ans and re.search(pat, t):
            return ans
    return None


def _format(thoughts: List[str], answer: str) -> str:
    c = get_crypto()
    lines = ["Resonance Field · DIMAX v3", "Ход размышлений:"]
    for i, th in enumerate(thoughts, 1):
        sig = c.sign_message(f"THOUGHT|{th}")[:24]
        lines.append(f"[{i}] {th}")
        lines.append(f"   🔏 {sig}…")
    lines.append("")
    lines.append(answer)
    lines.append(f"🔏 AKSI Identity: {c.sign_message(answer)[:32]}…")
    lines.append(f"DID: {c.get_did()}")
    return "\n".join(lines)


async def aksi_stream(
    message: str,
    mode: str = "aksi",
    history: Optional[List[Dict[str, str]]] = None,
    memory: str = "",
) -> AsyncGenerator[str, None]:
    history = history or []
    hit = _match(message)

    # try Ollama
    raw = ""
    if httpx is not None:
        prompt_parts = [SYSTEM, f"Режим: {mode}"]
        if memory:
            prompt_parts.append(f"Память: {memory}")
        for m in history[-8:]:
            role = "User" if m.get("role") == "user" else "АКСИ"
            prompt_parts.append(f"{role}: {m.get('content', '')}")
        prompt_parts.append(f"User: {message}\nАКСИ:")
        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                async with client.stream(
                    "POST",
                    OLLAMA_URL,
                    json={"model": OLLAMA_MODEL, "prompt": "\n".join(prompt_parts), "stream": True},
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
        # already streamed chunks; append signature footer
        footer = f"\n\n🔏 {get_crypto().sign_message(raw)[:32]}…"
        yield footer
        return

    thoughts = [
        f"Приняла сообщение ({len(message)} симв.).",
        "Сверяю identity и knowledge.",
        "Формирую ответ от имени АКСИ.",
    ]
    answer = hit or (
        "Слышу тебя. Уточни: identity, EQS, quantum, чат или админка — разберём."
    )
    full = _format(thoughts, answer)
    # stream by paragraphs
    for part in full.split("\n"):
        yield part + "\n"
