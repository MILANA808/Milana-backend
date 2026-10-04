"""Tests for the serializable AKSI discovery boundary."""
import unittest
from fastapi.testclient import TestClient
from main import app

class DiscoveryAPITest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    @staticmethod
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

    def test_protocol(self):
        r=self.client.get("/api/discovery/protocol")
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json()["protocol"],"AKSI-DISCOVERY/1")

    def test_plan_selects_discriminating_experiment(self):
        r=self.client.post("/api/discovery/plan",json=self.case())
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json()["selected"]["experiment_id"],"strong")
        self.assertTrue(r.json()["receipt"]["sha256"].startswith("sha256:"))

    def test_observation_records_survivor(self):
        body=self.case()
        body["experiment"]=body.pop("experiments")[1]
        body["output"]=3
        r=self.client.post("/api/discovery/observe",json=body)
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json()["evidence"]["survivors"],["B"])

if __name__=="__main__":
    unittest.main()
