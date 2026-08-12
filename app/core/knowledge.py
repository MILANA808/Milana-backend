"""Offline knowledge base for АКСИ"""
from __future__ import annotations

import re
from typing import Optional

from app.core.resonance import identity_block

KB = [
    (
        re.compile(r"кто ты|что ты|what are you|что такое акси", re.I),
        "Я АКСИ — суверенный ИИ. Identity, Resonance-подпись, память сессий. "
        "Работаю через Ollama локально + offline-знания. Без зависимости от OpenAI.",
    ),
    (
        re.compile(r"did|идентичност|подпись", re.I),
        None,  # dynamic
    ),
    (
        re.compile(r"небо.*голуб|почему.*небо", re.I),
        "Небо кажется голубым из‑за рассеяния Рэлея: молекулы воздуха сильнее "
        "рассеивают короткие (синие) волны солнечного света.",
    ),
    (
        re.compile(r"возможност|что умеешь|capabilities", re.I),
        "Чат, память сессий, Wikipedia/world search, кодекс, identity, admin, "
        "опционально Ollama LLM, P2P registry (roadmap).",
    ),
    (
        re.compile(r"привет|здравствуй|hello", re.I),
        "Здравствуйте. Я АКСИ — на связи.",
    ),
]


def lookup(text: str) -> Optional[str]:
    t = text or ""
    for pat, ans in KB:
        if not pat.search(t):
            continue
        if ans is None:
            idb = identity_block()
            return f"DID: {idb['did']}. Seed: {idb['seed']}. Contact: {idb['contact']}."
        return ans
    return None
