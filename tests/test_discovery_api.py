"""Tests for the serializable AKSI discovery boundary."""
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def case():
    return {
        "hypotheses": [
            {"id":"A","description":"y=x","predictions":[{"experiment_id":"weak","value":0},{"experiment_id":"strong","value":2}]},
            {"id":"B","description":"y=x+1","predictions":[{"experiment_id":"weak","value":1},{"experiment_id":"strong","value":3}]},
            {"id":"C","description":"y=2x","predictions":[{"experiment_id":"weak","value":0},{"experiment_id":"strong","value":4}]},
        ],
        "experiments": [
            {"id":"weak","input":0,"cost":1},
            {"id":"strong","input":2,"cost":1},
        ],
    }

def test_protocol():
    r=client.get("/api/discovery/protocol")
    assert r.status_code == 200
    assert r.json()["protocol"] == "AKSI-DISCOVERY/1"

def test_plan_selects_discriminating_experiment():
    r=client.post("/api/discovery/plan",json=case())
    assert r.status_code == 200
    assert r.json()["selected"]["experiment_id"] == "strong"
    assert r.json()["receipt"]["sha256"].startswith("sha256:")

def test_observation_records_survivor():
    body=case()
    body["experiment"]=body.pop("experiments")[1]
    body["output"]=3
    r=client.post("/api/discovery/observe",json=body)
    assert r.status_code == 200
    assert r.json()["evidence"]["survivors"] == ["B"]
