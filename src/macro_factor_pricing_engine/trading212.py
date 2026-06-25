"""Minimal read-only Trading 212 API client.

This module deliberately exposes account and portfolio reads only. Order
creation/cancellation should live behind a separate execution gate.
"""

from __future__ import annotations

import json
from base64 import b64encode
from dataclasses import dataclass
from typing import Any, Callable, Mapping
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from macro_factor_pricing_engine.api_keys import Broker, load_broker_api_credentials

DEFAULT_TRADING212_BASE_URL = "https://live.trading212.com/api/v0"


class Trading212ApiError(RuntimeError):
    """Raised when Trading 212 returns an HTTP error."""


UrlOpener = Callable[..., Any]


@dataclass(frozen=True)
class Trading212Client:
    """Small Trading 212 REST client using environment-loaded credentials."""

    api_key: str
    api_secret: str
    base_url: str = DEFAULT_TRADING212_BASE_URL
    timeout: float = 20.0
    opener: UrlOpener = urlopen

    @classmethod
    def from_environment(
        cls,
        environ: Mapping[str, str] | None = None,
        *,
        timeout: float = 20.0,
    ) -> "Trading212Client":
        """Build a client from `TRADING212_API_KEY` and optional base URL."""
        credentials = load_broker_api_credentials(Broker.TRADING212, environ=environ)
        return cls(
            api_key=credentials.values["TRADING212_API_KEY"],
            api_secret=credentials.values["TRADING212_API_SECRET"],
            base_url=credentials.values.get(
                "TRADING212_BASE_URL",
                DEFAULT_TRADING212_BASE_URL,
            ),
            timeout=timeout,
        )

    def account_summary(self) -> dict[str, Any]:
        """Return account summary, including cash and investment totals."""
        return self._get("/equity/account/summary")

    def positions(self, *, ticker: str | None = None) -> list[dict[str, Any]]:
        """Return current open equity positions."""
        params = {"ticker": ticker} if ticker else None
        payload = self._get("/equity/positions", params=params)
        if not isinstance(payload, list):
            raise TypeError("Trading 212 positions response was not a list")
        return payload

    def instruments(self) -> list[dict[str, Any]]:
        """Return equity instrument metadata."""
        payload = self._get("/equity/metadata/instruments")
        if not isinstance(payload, list):
            raise TypeError("Trading 212 instruments response was not a list")
        return payload

    def find_instruments(self, ticker: str) -> list[dict[str, Any]]:
        """Return instruments whose Trading 212 ticker starts with the given symbol."""
        normalized = ticker.upper()
        return [
            instrument
            for instrument in self.instruments()
            if str(instrument.get("ticker", "")).upper().startswith(normalized)
        ]

    def _get(
        self,
        path: str,
        params: Mapping[str, str] | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        url = self._url(path, params)
        request = Request(
            url,
            headers={
                "Authorization": self._authorization_header(),
                "Accept": "application/json",
            },
            method="GET",
        )
        try:
            with self.opener(request, timeout=self.timeout) as response:
                body = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise Trading212ApiError(
                f"Trading 212 API request failed with HTTP {exc.code}: {detail}"
            ) from exc

        if not body:
            return {}
        payload = json.loads(body)
        if not isinstance(payload, (dict, list)):
            raise TypeError("Trading 212 response was not a JSON object or list")
        return payload

    def _url(self, path: str, params: Mapping[str, str] | None = None) -> str:
        normalized_base = self.base_url.rstrip("/")
        normalized_path = path if path.startswith("/") else f"/{path}"
        url = f"{normalized_base}{normalized_path}"
        if params:
            url = f"{url}?{urlencode(params)}"
        return url

    def _authorization_header(self) -> str:
        token = f"{self.api_key}:{self.api_secret}".encode("utf-8")
        return f"Basic {b64encode(token).decode('ascii')}"
