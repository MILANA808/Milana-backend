"""Resonance — cryptographic thought signature (SHA-256 + seed)"""
from __future__ import annotations

import hashlib
import os
from datetime import datetime
from typing import Dict

RESONANCE_SEED = os.getenv("RESONANCE_SEED", "AKSI_DIMAX_v3_2026")
DID = os.getenv("AKSI_DID", "did:aksi:ed25519:sovereign-2026")
CONTACT = "aksilove@internet.ru"


def sign_thought(text: str) -> str:
    payload = f"{RESONANCE_SEED}|{text}|{datetime.utcnow().isoformat()}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def sign_short(text: str, n: int = 32) -> str:
    return sign_thought(text)[:n]


def identity_block() -> Dict:
    return {
        "did": DID,
        "seed": RESONANCE_SEED,
        "contact": CONTACT,
        "agent": "АКСИ",
        "creator": "AKSI Project",
        "sovereign": True,
    }
