import json
import unittest

from macro_factor_pricing_engine.trading212 import (
    DEFAULT_TRADING212_BASE_URL,
    Trading212Client,
)


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class Trading212ClientTests(unittest.TestCase):
    def test_client_loads_from_environment_without_exposing_secret(self):
        client = Trading212Client.from_environment(
            {
                "TRADING212_API_KEY": "key",
                "TRADING212_API_SECRET": "secret",
                "TRADING212_BASE_URL": "https://demo.trading212.com/api/v0",
            }
        )

        self.assertEqual(client.api_key, "key")
        self.assertEqual(client.api_secret, "secret")
        self.assertEqual(client.base_url, "https://demo.trading212.com/api/v0")

    def test_client_uses_live_base_url_by_default(self):
        client = Trading212Client.from_environment(
            {
                "TRADING212_API_KEY": "key",
                "TRADING212_API_SECRET": "secret",
            }
        )

        self.assertEqual(client.base_url, DEFAULT_TRADING212_BASE_URL)

    def test_account_summary_sends_basic_authorization_header(self):
        captured = {}

        def opener(request, timeout):
            captured["url"] = request.full_url
            captured["authorization"] = request.get_header("Authorization")
            captured["accept"] = request.get_header("Accept")
            captured["timeout"] = timeout
            return FakeResponse({"free": 12.34})

        client = Trading212Client(
            api_key="key",
            api_secret="secret",
            timeout=3.0,
            opener=opener,
        )
        payload = client.account_summary()

        self.assertEqual(payload, {"free": 12.34})
        self.assertEqual(
            captured["url"],
            "https://live.trading212.com/api/v0/equity/account/summary",
        )
        self.assertEqual(captured["authorization"], "Basic a2V5OnNlY3JldA==")
        self.assertEqual(captured["accept"], "application/json")
        self.assertEqual(captured["timeout"], 3.0)

    def test_positions_encodes_optional_ticker_filter(self):
        captured = {}

        def opener(request, timeout):
            captured["url"] = request.full_url
            return FakeResponse([{"ticker": "VUSA"}])

        client = Trading212Client(api_key="key", api_secret="secret", opener=opener)
        payload = client.positions(ticker="VUSA")

        self.assertEqual(payload, [{"ticker": "VUSA"}])
        self.assertEqual(
            captured["url"],
            "https://live.trading212.com/api/v0/equity/positions?ticker=VUSA",
        )

    def test_positions_requires_list_response(self):
        def opener(request, timeout):
            return FakeResponse({"unexpected": "shape"})

        client = Trading212Client(api_key="key", api_secret="secret", opener=opener)

        with self.assertRaises(TypeError):
            client.positions()

    def test_find_instruments_filters_by_ticker_prefix(self):
        def opener(request, timeout):
            return FakeResponse(
                [
                    {"ticker": "MU_US_EQ"},
                    {"ticker": "MUA_DE_EQ"},
                    {"ticker": "AAPL_US_EQ"},
                ]
            )

        client = Trading212Client(api_key="key", api_secret="secret", opener=opener)

        self.assertEqual(
            client.find_instruments("MU"),
            [{"ticker": "MU_US_EQ"}, {"ticker": "MUA_DE_EQ"}],
        )

    def test_empty_response_returns_empty_dict(self):
        class EmptyResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return b""

        def opener(request, timeout):
            return EmptyResponse()

        client = Trading212Client(api_key="key", api_secret="secret", opener=opener)

        self.assertEqual(client.account_summary(), {})


if __name__ == "__main__":
    unittest.main()
