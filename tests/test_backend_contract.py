"""Smoke tests for the public AKSI backend contract.

Run with: python -m unittest discover -s tests -p 'test_*.py'
"""
import unittest
from fastapi.testclient import TestClient
import main


class PublicContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(main.app)

    def test_health_is_machine_readable(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body.get("status"), "healthy")
        self.assertTrue(body.get("version"))
        self.assertTrue(body.get("timestamp"))

    def test_version_contract(self):
        response = self.client.get("/version")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("api"), "aksi-backend")
        self.assertTrue(response.json().get("version"))

    def test_echo_round_trip(self):
        payload = {"message": "AKSI contract check"}
        response = self.client.post("/echo", json=payload)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body.get("echo"), payload["message"])
        self.assertEqual(body.get("length"), len(payload["message"]))
        self.assertTrue(body.get("timestamp"))

    def test_proof_signature_is_verifiable_and_scope_is_limited(self):
        response = self.client.get("/aksi/proof")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body.get("verification", {}).get("verified"))
        self.assertEqual(body.get("verification", {}).get("algorithm"), "Ed25519")
        self.assertEqual(body.get("verification", {}).get("scope"), "signature integrity only")
        self.assertIn("does not establish factual truth", body.get("verification", {}).get("claim_boundary", ""))

    def test_readiness_separates_runtime_from_signing_key_warning(self):
        response = self.client.get("/ready")
        self.assertIn(response.status_code, (200, 503))
        body = response.json()
        self.assertIn("ready", body)
        self.assertIn("reasons", body)
        self.assertIn("warnings", body)
        if body.get("signing_key_mode") in ("ephemeral", "unavailable"):
            self.assertIn(f"signing_identity_{body['signing_key_mode']}", body["warnings"])
            self.assertNotIn(f"signing_identity_{body['signing_key_mode']}", body["reasons"])

    def test_virtual_cluster_route_is_mounted_and_discloses_simulation(self):
        response = self.client.get("/aksi/cluster/status")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body.get("kind"), "classical-cpu-simulation")
        self.assertFalse(body.get("gpu_hardware_present"))

    def test_metrics_is_json_and_timestamped(self):
        response = self.client.get("/aksi/metrics")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("timestamp", body)
        self.assertIsInstance(body.get("ai_code_work"), dict)


if __name__ == "__main__":
    unittest.main()
