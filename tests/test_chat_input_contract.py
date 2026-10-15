"""Input-boundary tests for the public AKSI chat API."""
import unittest
from fastapi.testclient import TestClient
import main


class ChatInputContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(main.app)

    def test_chat_rejects_empty_message(self):
        response = self.client.post("/api/chat", json={"message": "   "})
        self.assertEqual(response.status_code, 422)

    def test_chat_rejects_overlong_message_before_generation(self):
        response = self.client.post("/api/chat", json={"message": "x" * 12001})
        self.assertEqual(response.status_code, 422)

    def test_chat_rejects_invalid_session_id(self):
        response = self.client.post("/api/chat", json={"message": "hello", "session_id": "../other-user"})
        self.assertEqual(response.status_code, 422)

    def test_stream_route_validates_same_contract(self):
        response = self.client.post("/api/chat/stream", json={"message": "hello", "session_id": "bad session"})
        self.assertEqual(response.status_code, 422)

    def test_legacy_content_field_remains_supported(self):
        # Empty content is validated without invoking a model/provider.
        response = self.client.post("/api/chat", json={"content": " "})
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
