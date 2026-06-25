"""Minimal read-only IG REST API client."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable, Mapping
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from macro_factor_pricing_engine.api_keys import Broker, load_broker_api_credentials

DEFAULT_IG_DEMO_BASE_URL = "https://demo-api.ig.com/gateway/deal"
DEFAULT_IG_LIVE_BASE_URL = "https://api.ig.com/gateway/deal"


class IgApiError(RuntimeError):
    """Raised when IG returns an HTTP error."""


UrlOpener = Callable[..., Any]


@dataclass(frozen=True)
class IgSession:
    """IG session tokens for authenticated read requests."""

    payload: dict[str, Any]
    cst: str = ""
    security_token: str = ""
    access_token: str = ""
    account_id: str = ""


@dataclass(frozen=True)
class IgClient:
    """Small IG REST client using environment-loaded credentials."""

    api_key: str
    username: str
    password: str
    base_url: str = DEFAULT_IG_DEMO_BASE_URL
    timeout: float = 20.0
    opener: UrlOpener = urlopen

    @classmethod
    def from_environment(
        cls,
        environ: Mapping[str, str] | None = None,
        *,
        timeout: float = 20.0,
    ) -> "IgClient":
        """Build a client from IG environment variables."""
        credentials = load_broker_api_credentials(Broker.IG_GROUP, environ=environ)
        account_type = credentials.values.get("IG_ACCOUNT_TYPE", "demo").lower()
        default_base_url = (
            DEFAULT_IG_LIVE_BASE_URL
            if account_type == "live"
            else DEFAULT_IG_DEMO_BASE_URL
        )
        return cls(
            api_key=credentials.values["IG_API_KEY"],
            username=credentials.values["IG_USERNAME"],
            password=credentials.values["IG_PASSWORD"],
            base_url=credentials.values.get("IG_BASE_URL", default_base_url),
            timeout=timeout,
        )

    def create_session(self, *, version: str = "3") -> IgSession:
        """Create an IG session and capture OAuth or CST/security tokens."""
        body: dict[str, Any] = {
            "identifier": self.username,
            "password": self.password,
        }
        if version == "2":
            body["encryptedPassword"] = False
        request = Request(
            self._url("/session"),
            data=json.dumps(body).encode("utf-8"),
            headers={
                "X-IG-API-KEY": self.api_key,
                "VERSION": version,
                "Accept": "application/json",
                "Content-Type": "application/json; charset=UTF-8",
            },
            method="POST",
        )
        response, headers = self._request(request)
        cst = headers.get("CST", "")
        security_token = headers.get("X-SECURITY-TOKEN", "")
        if not isinstance(response, dict):
            raise TypeError("IG session response was not a JSON object")
        oauth = response.get("oauthToken", {})
        access_token = oauth.get("access_token", "") if isinstance(oauth, dict) else ""
        if not access_token and (not cst or not security_token):
            raise IgApiError("IG session response did not include OAuth or CST/security tokens")
        return IgSession(
            payload=response,
            cst=cst,
            security_token=security_token,
            access_token=access_token,
            account_id=str(response.get("accountId") or response.get("currentAccountId") or ""),
        )

    def accounts(self, session: IgSession) -> dict[str, Any]:
        """Return IG account details for the active session."""
        payload = self._authenticated_get("/accounts", session)
        if not isinstance(payload, dict):
            raise TypeError("IG accounts response was not a JSON object")
        return payload

    def market(self, epic: str, session: IgSession) -> dict[str, Any]:
        """Return market details for one IG epic."""
        payload = self._authenticated_get(f"/markets/{epic}", session)
        if not isinstance(payload, dict):
            raise TypeError("IG market response was not a JSON object")
        return payload

    def _authenticated_get(
        self,
        path: str,
        session: IgSession,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        request = Request(
            self._url(path),
            headers=self._auth_headers(session),
            method="GET",
        )
        payload, _headers = self._request(request)
        return payload

    def _auth_headers(self, session: IgSession) -> dict[str, str]:
        headers = {
            "X-IG-API-KEY": self.api_key,
            "VERSION": "1",
            "Accept": "application/json",
        }
        if session.access_token:
            headers["Authorization"] = f"Bearer {session.access_token}"
            if session.account_id:
                headers["IG-ACCOUNT-ID"] = session.account_id
        else:
            headers["CST"] = session.cst
            headers["X-SECURITY-TOKEN"] = session.security_token
        return headers

    def _request(self, request: Request) -> tuple[dict[str, Any] | list[dict[str, Any]], Any]:
        try:
            with self.opener(request, timeout=self.timeout) as response:
                body = response.read().decode("utf-8")
                headers = response.headers
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise IgApiError(f"IG API request failed with HTTP {exc.code}: {detail}") from exc

        if not body:
            return {}, headers
        payload = json.loads(body)
        if not isinstance(payload, (dict, list)):
            raise TypeError("IG response was not a JSON object or list")
        return payload, headers

    def _url(self, path: str) -> str:
        normalized_base = self.base_url.rstrip("/")
        normalized_path = path if path.startswith("/") else f"/{path}"
        return f"{normalized_base}{normalized_path}"
