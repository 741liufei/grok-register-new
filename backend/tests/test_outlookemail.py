import unittest

from backend.email_providers import outlookemail


class FakeResponse:
    def __init__(self, data, status_code=200, headers=None):
        self._data = data
        self.status_code = status_code
        self.headers = headers or {}

    def json(self):
        return self._data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeSession:
    def __init__(self, server):
        self.server = server
        self.cookies = {}
        self.proxies = None

    def post(self, url, **kwargs):
        self.server["login_calls"] += 1
        self.server["login_payloads"].append(kwargs.get("json"))
        return FakeResponse({"success": True, "launch_url": "/extension-login/once"})

    def get(self, url, **kwargs):
        if "/extension-login/" in url:
            self.cookies["session"] = f"session-{self.server['login_calls']}"
            return FakeResponse({}, headers={"set-cookie": "session=ignored; Path=/"})
        if url.endswith("/api/csrf-token"):
            self.server["csrf_headers"].append(dict(kwargs.get("headers") or {}))
            status_code = (
                self.server["csrf_statuses"].pop(0)
                if self.server["csrf_statuses"]
                else 200
            )
            if status_code != 200:
                return FakeResponse({"success": False}, status_code=status_code)
            return FakeResponse(
                {"csrf_token": "csrf-value", "csrf_disabled": False},
                headers={"set-cookie": "csrf_session=bound; Path=/"},
            )
        raise AssertionError(url)

    def put(self, url, **kwargs):
        self.server["put_calls"].append(
            {
                "url": url,
                "headers": dict(kwargs.get("headers") or {}),
                "json": kwargs.get("json"),
            }
        )
        return FakeResponse({"success": True, "message": "状态更新成功"})


class OutlookEmailDisableTests(unittest.TestCase):
    def setUp(self):
        outlookemail.reset_runtime_state()
        self.server = {
            "login_calls": 0,
            "login_payloads": [],
            "csrf_headers": [],
            "csrf_statuses": [],
            "put_calls": [],
        }

    def session_factory(self):
        return FakeSession(self.server)

    @staticmethod
    def http_get(url, **kwargs):
        if url.endswith("/api/external/accounts"):
            return FakeResponse(
                {
                    "success": True,
                    "accounts": [
                        {"id": 367, "email": "fixture@outlook.com", "status": "active"}
                    ],
                }
            )
        raise AssertionError(url)

    def test_password_login_csrf_and_put_inactive(self):
        email, _ = outlookemail.acquire_email(
            self.http_get,
            self.session_factory,
            "http://mail-pool.test",
            api_key="api-key",
            source="accounts",
            pick_mode="sequential",
        )
        result = outlookemail.disable_account(
            self.http_get,
            self.session_factory,
            "http://mail-pool.test",
            email,
            api_key="api-key",
            web_password="web-password",
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["account_id"], 367)
        self.assertEqual(self.server["login_calls"], 1)
        self.assertEqual(
            self.server["login_payloads"],
            [{"password": "web-password", "next": "/"}],
        )
        self.assertEqual(len(self.server["put_calls"]), 1)
        request = self.server["put_calls"][0]
        self.assertTrue(request["url"].endswith("/api/accounts/367"))
        self.assertEqual(request["json"], {"status": "inactive"})
        self.assertEqual(request["headers"]["X-CSRFToken"], "csrf-value")
        self.assertNotIn("Cookie", request["headers"])

    def test_already_inactive_is_idempotent_without_login(self):
        def inactive_get(url, **kwargs):
            return FakeResponse(
                {
                    "success": True,
                    "accounts": [
                        {"id": 8, "email": "inactive@outlook.com", "status": "inactive"}
                    ],
                }
            )

        result = outlookemail.disable_account(
            inactive_get,
            self.session_factory,
            "http://mail-pool.test",
            "inactive@outlook.com",
            api_key="api-key",
        )
        self.assertTrue(result["success"])
        self.assertTrue(result["already_inactive"])
        self.assertEqual(self.server["login_calls"], 0)
        self.assertEqual(self.server["put_calls"], [])

    def test_expired_session_refreshes_password_login_once(self):
        self.server["csrf_statuses"] = [401, 200]
        result = outlookemail.disable_account(
            self.http_get,
            self.session_factory,
            "http://mail-pool.test",
            "fixture@outlook.com",
            api_key="api-key",
            web_password="web-password",
        )
        self.assertTrue(result["success"])
        self.assertEqual(self.server["login_calls"], 2)
        self.assertEqual(len(self.server["put_calls"]), 1)

    def test_http_error_includes_request_and_response_details(self):
        class ErrorResponse(FakeResponse):
            text = '{"success":false,"error":"invalid status"}'

            def raise_for_status(self):
                return None

        def error_session_factory():
            session = FakeSession(self.server)

            def put(url, **kwargs):
                self.server["put_calls"].append(
                    {"url": url, "headers": dict(kwargs.get("headers") or {}), "json": kwargs.get("json")}
                )
                return ErrorResponse({"success": False, "error": "invalid status"}, status_code=400)

            session.put = put
            return session

        with self.assertRaisesRegex(
            Exception,
            r"停用请求失败: HTTP 400; url=.*/api/accounts/367; request_body=\{'status': 'inactive'\}; response_body=",
        ):
            outlookemail.disable_account(
                self.http_get,
                error_session_factory,
                "http://mail-pool.test",
                "fixture@outlook.com",
                api_key="api-key",
                web_password="web-password",
            )

    def test_rotated_csrf_session_cookie_is_sent_by_session_jar(self):
        class RotatingSession(FakeSession):
            def get(self, url, **kwargs):
                if url.endswith("/api/csrf-token"):
                    self.cookies["session"] = "rotated-session"
                    return FakeResponse({"csrf_token": "csrf-value", "csrf_disabled": False})
                return super().get(url, **kwargs)

            def put(self, url, **kwargs):
                headers = dict(kwargs.get("headers") or {})
                self.server["put_calls"].append({"url": url, "headers": headers, "json": kwargs.get("json")})
                assert headers.get("X-CSRFToken") == "csrf-value"
                assert "Cookie" not in headers
                assert self.cookies.get("session") == "rotated-session"
                return FakeResponse({"success": True})

        def factory():
            return RotatingSession(self.server)

        result = outlookemail.disable_account(
            self.http_get,
            factory,
            "http://mail-pool.test",
            "fixture@outlook.com",
            api_key="api-key",
            session_cookie="session=initial",
        )
        self.assertTrue(result["success"])


if __name__ == "__main__":
    unittest.main()
