import json
import unittest
from email.message import Message

from macro_factor_pricing_engine.ig import (
    DEFAULT_IG_DEMO_BASE_URL,
    DEFAULT_IG_LIVE_BASE_URL,
    IgClient,
    IgSession,
)


class FakeResponse:
    def __init__(self, payload, headers=None):
        self.payload = payload
        self.headers = Message()
        for name, value in (headers or {}).items():
            self.headers[name] = value

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class IgClientTests(unittest.TestCase):
    def test_client_loads_demo_environment_defaults(self):
        client = IgClient.from_environment(
            {
                "IG_API_KEY": "key",
                "IG_USERNAME": "user",
                "IG_PASSWORD": "password",
                "IG_ACCOUNT_TYPE": "demo",
            }
        )

        self.assertEqual(client.api_key, "key")
        self.assertEqual(client.username, "user")
        self.assertEqual(client.password, "password")
        self.assertEqual(client.base_url, DEFAULT_IG_DEMO_BASE_URL)

    def test_client_loads_live_environment_defaults(self):
        client = IgClient.from_environment(
            {
                "IG_API_KEY": "key",
                "IG_USERNAME": "user",
                "IG_PASSWORD": "password",
                "IG_ACCOUNT_TYPE": "live",
            }
        )

        self.assertEqual(client.base_url, DEFAULT_IG_LIVE_BASE_URL)

    def test_create_session_posts_credentials_and_extracts_tokens(self):
        captured = {}

        def opener(request, timeout):
            captured["url"] = request.full_url
            captured["method"] = request.get_method()
            captured["api_key"] = request.get_header("X-ig-api-key")
            captured["version"] = request.get_header("Version")
            captured["body"] = json.loads(request.data.decode("utf-8"))
            captured["timeout"] = timeout
            return FakeResponse(
                {
                    "accountId": "ABC123",
                    "oauthToken": {
                        "access_token": "oauth-token",
                        "token_type": "Bearer",
                    },
                },
            )

        client = IgClient(
            api_key="key",
            username="user",
            password="password",
            opener=opener,
            timeout=3.0,
        )
        session = client.create_session()

        self.assertEqual(
            captured["url"],
            "https://demo-api.ig.com/gateway/deal/session",
        )
        self.assertEqual(captured["method"], "POST")
        self.assertEqual(captured["api_key"], "key")
        self.assertEqual(captured["version"], "3")
        self.assertEqual(
            captured["body"],
            {
                "identifier": "user",
                "password": "password",
            },
        )
        self.assertEqual(captured["timeout"], 3.0)
        self.assertEqual(session.access_token, "oauth-token")
        self.assertEqual(session.account_id, "ABC123")
        self.assertEqual(session.payload["accountId"], "ABC123")

    def test_create_session_version_2_extracts_cst_tokens(self):
        captured = {}

        def opener(request, timeout):
            captured["version"] = request.get_header("Version")
            captured["body"] = json.loads(request.data.decode("utf-8"))
            return FakeResponse(
                {"currentAccountId": "ABC123"},
                {"CST": "client-token", "X-SECURITY-TOKEN": "account-token"},
            )

        client = IgClient(
            api_key="key",
            username="user",
            password="password",
            opener=opener,
        )
        session = client.create_session(version="2")

        self.assertEqual(captured["version"], "2")
        self.assertEqual(captured["body"]["encryptedPassword"], False)
        self.assertEqual(session.cst, "client-token")
        self.assertEqual(session.security_token, "account-token")
        self.assertEqual(session.account_id, "ABC123")

    def test_accounts_sends_oauth_session_token(self):
        captured = {}

        def opener(request, timeout):
            captured["url"] = request.full_url
            captured["api_key"] = request.get_header("X-ig-api-key")
            captured["authorization"] = request.get_header("Authorization")
            captured["account_id"] = request.get_header("Ig-account-id")
            captured["version"] = request.get_header("Version")
            return FakeResponse({"accounts": []})

        client = IgClient(api_key="key", username="user", password="password", opener=opener)
        payload = client.accounts(
            IgSession(payload={}, access_token="oauth-token", account_id="ABC123")
        )

        self.assertEqual(payload, {"accounts": []})
        self.assertEqual(
            captured["url"],
            "https://demo-api.ig.com/gateway/deal/accounts",
        )
        self.assertEqual(captured["api_key"], "key")
        self.assertEqual(captured["authorization"], "Bearer oauth-token")
        self.assertEqual(captured["account_id"], "ABC123")
        self.assertEqual(captured["version"], "1")


if __name__ == "__main__":
    unittest.main()
