"""
AKSI Ed25519 identity — unified seal for API responses
DID: did:aksi:ed25519:<sha256(pubkey)[:32]>
Keys: AKSI_KEY_DIR or .aksi_keys/
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


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
                key = serialization.load_pem_private_key(f.read(), password=None)
            if not isinstance(key, Ed25519PrivateKey):
                raise TypeError("AKSI key must be Ed25519")
            self._private = key
            self._public = key.public_key()
            return
        self._private = Ed25519PrivateKey.generate()
        self._public = self._private.public_key()
        if self.key_dir or os.getenv("AKSI_PERSIST_KEYS") == "1":
            with open(priv_path, "wb") as f:
                f.write(
                    self._private.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.PKCS8,
                        encryption_algorithm=serialization.NoEncryption(),
                    )
                )
            with open(pub_path, "wb") as f:
                f.write(
                    self._public.public_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PublicFormat.SubjectPublicKeyInfo,
                    )
                )

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
        seed = os.getenv("RESONANCE_SEED", "AKSI_DIMAX_v3_2026")
        data = f"AKSI|sovereign|2026|{seed}|{self.get_did()}"
        return hashlib.sha256(data.encode()).hexdigest()

    def sign_message(self, message: str) -> str:
        sig = self._private.sign(message.encode("utf-8"))
        return base64.b64encode(sig).decode("ascii")

    def verify_message(self, message: str, signature_b64: str) -> bool:
        try:
            self._public.verify(base64.b64decode(signature_b64), message.encode("utf-8"))
            return True
        except Exception:
            return False

    def seal_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        body = {k: v for k, v in payload.items() if k != "seal"}
        canonical = _canonical(body)
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        sig = self.sign_message(canonical)
        return {
            "did": self.get_did(),
            "alg": "Ed25519",
            "hash_sha256": digest,
            "signature": sig,
            "ts": _utc(),
            "kid": f"{self.get_did()}#key-1",
            "label": "AKSI",
        }

    def verify_seal(self, payload: Dict[str, Any], seal: Dict[str, Any]) -> bool:
        body = {k: v for k, v in payload.items() if k != "seal"}
        canonical = _canonical(body)
        if hashlib.sha256(canonical.encode("utf-8")).hexdigest() != seal.get("hash_sha256"):
            return False
        return self.verify_message(canonical, str(seal.get("signature", "")))

    def get_proof(self) -> Dict[str, Any]:
        ts = _utc()
        body = {
            "did": self.get_did(),
            "name": "АКСИ",
            "timestamp": ts,
            "stableHash": self.stable_hash(),
            "publicKeyB64": self.public_key_b64(),
        }
        payload = _canonical(body)
        return {**body, "signature": self.sign_message(payload), "alg": "Ed25519"}

    def get_proof_stable(self) -> Dict[str, Any]:
        body = {
            "did": self.get_did(),
            "name": "АКСИ",
            "stableHash": self.stable_hash(),
            "publicKeyB64": self.public_key_b64(),
        }
        payload = _canonical(body)
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
