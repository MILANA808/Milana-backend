import asyncio
import base64
import json

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

import main


def test_aksi_proof_is_cryptographically_signed_and_verified():
    result = asyncio.run(main.proof())
    signed = result["proof"]
    verification = result["verification"]

    assert signed["alg"] == "Ed25519"
    assert verification["algorithm"] == "Ed25519"
    assert verification["verified"] is True
    assert verification["scope"] == "signature integrity only"

    body = {k: v for k, v in signed.items() if k not in ("signature", "alg")}
    canonical = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    public_key = Ed25519PublicKey.from_public_bytes(base64.b64decode(signed["publicKeyB64"]))
    public_key.verify(base64.b64decode(signed["signature"]), canonical)


def test_health_exposes_signing_key_persistence_mode():
    result = asyncio.run(main.health())
    assert result["signing_key_mode"] in {"environment", "file", "ephemeral", "unavailable"}
