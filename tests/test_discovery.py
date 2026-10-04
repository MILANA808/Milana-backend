from fastapi.testclient import TestClient

from main import app
from app.science.discovery import DiscoveryEngine, Experiment, Hypothesis


def payload():
    return {
        "hypotheses": [
            {
                "id": "H1",
                "description": "rule A",
                "predictions": [
                    {"experiment_id": "E1", "value": "red"},
                    {"experiment_id": "E2", "value": "circle"},
                ],
            },
            {
                "id": "H2",
                "description": "rule B",
                "predictions": [
                    {"experiment_id": "E1", "value": "blue"},
                    {"experiment_id": "E2", "value": "circle"},
                ],
            },
        ],
        "experiments": [
            {"id": "E1", "input": "test-1", "cost": 1},
            {"id": "E2", "input": "test-2", "cost": 1},
        ],
    }


def test_engine_selects_discriminating_experiment():
    hs = [
        Hypothesis("H1", "A", lambda x: "red" if x == 1 else "circle"),
        Hypothesis("H2", "B", lambda x: "blue" if x == 1 else "circle"),
    ]
    result = DiscoveryEngine(hs).choose_experiment(
        [Experiment("E1", 1), Experiment("E2", 2)]
    )
    assert result["selected"]["experiment_id"] == "E1"
    assert result["selected"]["partition_count"] == 2


def test_discovery_api_is_registered():
    client = TestClient(app)
    r = client.get("/api/discovery/protocol")
    assert r.status_code == 200
    assert r.json()["protocol"] == "AKSI-DISCOVERY/1"


def test_discovery_plan_and_synthetic_receipts():
    client = TestClient(app)
    data = payload()

    plan = client.post("/api/discovery/plan", json=data)
    assert plan.status_code == 200
    body = plan.json()
    assert body["ok"] is True
    assert body["selected"]["experiment_id"] == "E1"
    assert body["receipt"]["sha256"].startswith("sha256:")

    synthetic = client.post("/api/discovery/synthetic", json=data)
    assert synthetic.status_code == 200
    body = synthetic.json()
    assert body["ok"] is True
    assert body["evidence"]["selected_experiment"] == "E1"
    assert body["evidence"]["observation"] == "red"
    assert body["receipt"]["sha256"].startswith("sha256:")


def test_observation_keeps_only_matching_hypotheses():
    client = TestClient(app)
    data = payload()
    req = {
        "hypotheses": data["hypotheses"],
        "experiment": data["experiments"][0],
        "output": "blue",
    }
    r = client.post("/api/discovery/observe", json=req)
    assert r.status_code == 200
    assert r.json()["evidence"]["survivors"] == ["H2"]
