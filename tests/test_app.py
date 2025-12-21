import os
from pathlib import Path

import pytest

try:
    from fastapi.testclient import TestClient
    import app.main as main
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False
    main = None  # type: ignore
    TestClient = None  # type: ignore

client = TestClient(main.app) if HAS_FASTAPI else None


def setup_function(_):
    if not HAS_FASTAPI:
        return
    # Сбросим лимитер и логи между тестами
    main._hits.clear()
    main._logs.clear()
    proof = Path("PROOF_SHA256.txt")
    if proof.exists():
        proof.unlink()


def test_root_summary():
    if not HAS_FASTAPI:
        pytest.skip("FastAPI не установлена")
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["service"] == "AKSI Bot Backend"
    assert "/health" in data["endpoints"]


def test_health_and_version():
    if not HAS_FASTAPI:
        pytest.skip("FastAPI не установлена")
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

    ver = client.get("/version").json()["version"]
    assert ver == os.getenv("AKSI_VERSION", "0.1.0")


def test_echo_and_metrics():
    if not HAS_FASTAPI:
        pytest.skip("FastAPI не установлена")
    payload = {"data": {"hello": "world"}}
    resp = client.post("/echo", json=payload)
    assert resp.status_code == 200
    assert resp.json() == payload

    metrics = client.get("/aksi/metrics").json()
    assert metrics["ok"] is True
    assert metrics["version"] == os.getenv("AKSI_VERSION", "0.1.0")


def test_eqs_demo_mode():
    if not HAS_FASTAPI:
        pytest.skip("FastAPI не установлена")
    resp = client.post("/eqs/score", json={"text": "любовь и свет"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["score"] >= 50


def test_psi_demo_mode():
    if not HAS_FASTAPI:
        pytest.skip("FastAPI не установлена")
    resp = client.post("/psi/state", json={"omega": 1.0, "phi": 2.0, "amplitude": 3.0})
    assert resp.status_code == 200
    assert resp.json()["psi"] == 3.0


def test_proof_stable_persists():
    if not HAS_FASTAPI:
        pytest.skip("FastAPI не установлена")
    resp1 = client.post("/aksi/proof/stable")
    assert resp1.status_code == 200
    digest1 = resp1.json()["sha256"]

    resp2 = client.post("/aksi/proof/stable")
    assert resp2.status_code == 200
    digest2 = resp2.json()["sha256"]

    assert digest1 == digest2
