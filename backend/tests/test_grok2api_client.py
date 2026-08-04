import json
import tempfile
import unittest
from pathlib import Path

from backend.integrations.grok2api_client import (
    Grok2APIImportError,
    import_auth_file,
    import_with_credentials,
    login,
)


class FakeResponse:
    def __init__(self, status=200, payload=None, lines=None):
        self.status_code = status
        self._payload = payload
        self._lines = lines or []
        self.closed = False

    def json(self):
        return self._payload

    def iter_lines(self):
        return iter(self._lines)

    def close(self):
        self.closed = True


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def post(self, url, **kwargs):
        if "multipart" in kwargs:
            kwargs = dict(kwargs)
        self.calls.append((url, kwargs))
        return self.responses.pop(0)


class Grok2APIClientTests(unittest.TestCase):
    def test_login_returns_fresh_access_token(self):
        session = FakeSession(
            [FakeResponse(payload={"data": {"tokens": {"accessToken": "fresh-token"}}})]
        )
        token = login("https://example.test/", "admin", "secret", session=session)
        self.assertEqual(token, "fresh-token")
        self.assertEqual(session.calls[0][0], "https://example.test/api/admin/v1/auth/login")
        self.assertEqual(session.calls[0][1]["json"], {"username": "admin", "password": "secret"})

    def test_import_uses_files_field_and_parses_complete_event(self):
        response = FakeResponse(
            lines=[
                b": connected",
                b"",
                b"event: progress",
                b'data: {"completed":1,"total":1}',
                b"",
                b"event: complete",
                b'data: {"created":1,"updated":0,"synced":1}',
                b"",
            ]
        )
        session = FakeSession([response])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "g2a-fixture.json"
            path.write_text(json.dumps({"provider": "grok_build"}), encoding="utf-8")
            result = import_auth_file("https://example.test", "token", path, session=session)
        self.assertEqual(result["created"], 1)
        self.assertIn("multipart", session.calls[0][1])
        self.assertTrue(response.closed)

    def test_import_surfaces_sse_error(self):
        session = FakeSession(
            [FakeResponse(lines=[b"event: error", b'data: {"message":"fixture failed"}', b""])]
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "g2a-fixture.json"
            path.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(Grok2APIImportError, "fixture failed"):
                import_auth_file("https://example.test", "token", path, session=session)

    def test_import_with_credentials_logs_in_before_upload(self):
        session = FakeSession(
            [
                FakeResponse(payload={"data": {"tokens": {"accessToken": "fresh-token"}}}),
                FakeResponse(lines=[b"event: complete", b'data: {"created":0,"updated":1}', b""]),
            ]
        )
        config = {
            "grok2api_remote_url": "https://example.test",
            "grok2api_remote_username": "admin",
            "grok2api_remote_password": "secret",
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "g2a-fixture.json"
            path.write_text("{}", encoding="utf-8")
            result = import_with_credentials(config, path, session=session)
        self.assertEqual(result["updated"], 1)
        self.assertEqual(len(session.calls), 2)
        self.assertEqual(
            session.calls[1][1]["headers"]["Authorization"], "Bearer fresh-token"
        )


if __name__ == "__main__":
    unittest.main()
