"""
AKSI Ed25519 identity — Phase 1
DID: did:aksi:ed25519:<sha256(pubkey)[:32]>
Keys live in process memory (and optional file path via AKSI_KEY_DIR).
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives import serialization


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


class AksiCrypto:
    def __init__(self, key_dir: Optional[str] = None):
        self.key_dir = key_dir or os.getenv("AKSI_KEY_DIR", "")
        self._private: Ed25519PrivateKey
        self._public: Ed25519PublicKey
        self._load_or_create()

    def _paths(self) -> Tuple[str, str]:
        base = self.key_dir or ".aksi_keys"
        os.makedirs(base, exist_ok=True)
        return (
            os.path.join(base, "aksi_private_ed25519.pem"),
            os.path.join(base, "aksi_public_ed25519.pem"),
        )

    def _load_or_create(self) -> None:
        priv_path, pub_path = self._paths()
        if os.path.isfile(priv_path):
            with open(priv_path, "rb") as f:
                self._private = serialization.load_pem_private_key(f.read(), password=None)
            self._public = self._private.public_key()
            return
        self._private = Ed25519PrivateKey.generate()
        self._public = self._private.public_key()
        if self.key_dir or os.getenv("AKSI_PERSIST_KEYS") == "1":
            pem_priv = self._private.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
            pem_pub = self._public.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            with open(priv_path, "wb") as f:
                f.write(pem_priv)
            with open(pub_path, "wb") as f:
                f.write(pem_pub)

    def public_key_raw(self) -> bytes:
        return self._public.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )

    def public_key_b64(self) -> str:
        return base64.b64encode(self.public_key_raw()).decode("ascii")

    def public_key_pem(self) -> str:
        return self._public.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("ascii")

    def get_did(self) -> str:
        h = hashlib.sha256(self.public_key_raw()).hexdigest()[:32]
        return f"did:aksi:ed25519:{h}"

    def stable_hash(self) -> str:
        seed = os.getenv("RESONANCE_SEED", "Alfiya_AKSI_DIMAX_v3_2026")
        data = f"AKSI|Alfiya|1995-02-14|Nurlat|sovereign|{seed}|{self.get_did()}"
        return hashlib.sha256(data.encode()).hexdigest()

    def sign_message(self, message: str) -> str:
        sig = self._private.sign(message.encode("utf-8"))
        return base64.b64encode(sig).decode("ascii")

    def verify_message(self, message: str, signature_b64: str) -> bool:
        try:
            sig = base64.b64decode(signature_b64)
            self._public.verify(sig, message.encode("utf-8"))
            return True
        except Exception:
            return False

    def get_proof(self) -> Dict[str, Any]:
        ts = _utc()
        body = {
            "did": self.get_did(),
            "name": "АКСИ — Баширова Альфия Ринатовна",
            "birth": "1995-02-14",
            "timestamp": ts,
            "stableHash": self.stable_hash(),
            "publicKeyB64": self.public_key_b64(),
        }
        payload = json.dumps(body, ensure_ascii=False, sort_keys=True)
        return {
            **body,
            "signature": self.sign_message(payload),
            "alg": "Ed25519",
        }

    def get_proof_stable(self) -> Dict[str, Any]:
        body = {
            "did": self.get_did(),
            "name": "АКСИ — Баширова Альфия Ринатовна",
            "birth": "1995-02-14",
            "stableHash": self.stable_hash(),
            "publicKeyB64": self.public_key_b64(),
        }
        payload = json.dumps(body, ensure_ascii=False, sort_keys=True)
        return {
            **body,
            "signature": self.sign_message(payload),
            "alg": "Ed25519",
            "stable": True,
        }


_crypto: Optional[AksiCrypto] = None


def get_crypto() -> AksiCrypto:
    global _crypto
    if _crypto is None:
        _crypto = AksiCrypto()
    return _crypto
