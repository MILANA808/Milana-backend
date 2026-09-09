import hashlib
import unittest

from fastapi import HTTPException

from app.api.web_gateway import _clean_text, _evidence, _validate_url


class InternetGatewayTests(unittest.TestCase):
    def test_allows_public_https_shape(self):
        self.assertEqual(_validate_url("https://example.com/path"), "https://example.com/path")

    def test_rejects_non_http_schemes(self):
        with self.assertRaises(HTTPException):
            _validate_url("file:///etc/passwd")

    def test_rejects_localhost(self):
        with self.assertRaises(HTTPException):
            _validate_url("http://127.0.0.1:8000/")

    def test_rejects_private_network(self):
        with self.assertRaises(HTTPException):
            _validate_url("http://192.168.1.10/")

    def test_rejects_url_credentials(self):
        with self.assertRaises(HTTPException):
            _validate_url("https://user:pass@example.com/")

    def test_evidence_hash_matches_payload(self):
        text = "AKSI evidence"
        item = _evidence("https://example.com", "Example", text, "text/html", "test")
        self.assertEqual(item["content_sha256"], hashlib.sha256(text.encode()).hexdigest())
        self.assertEqual(item["source_id"], "sha256:" + item["content_sha256"])
        self.assertEqual(item["trust"], "unverified")

    def test_html_cleaner_removes_executable_content(self):
        cleaned = _clean_text("<script>alert(1)</script><h1>Hello</h1><style>x{}</style>")
        self.assertEqual(cleaned, "Hello")


if __name__ == "__main__":
    unittest.main()
