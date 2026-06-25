"""Broker API setup registry and environment-based credential loading.

This module is deliberately credential-only. It does not create broker clients,
open sessions, or submit orders.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from typing import Mapping


class Broker(str, Enum):
    """Broker identifiers supported by the API setup registry."""

    TRADING212 = "trading212"
    INTERACTIVE_BROKERS = "interactive_brokers"
    ROBINHOOD = "robinhood"
    IG_GROUP = "ig_group"
    CAPITAL_COM = "capital_com"
    PLUS500 = "plus500"


@dataclass(frozen=True)
class BrokerApiSetup:
    """Static setup metadata for one broker API."""

    broker: Broker
    display_name: str
    required_env_vars: tuple[str, ...]
    optional_env_vars: tuple[str, ...]
    default_base_url_env_var: str | None
    docs_url: str
    auth_note: str
    execution_supported: bool
    safety_note: str


@dataclass(frozen=True)
class BrokerApiStatus:
    """Readiness summary without exposing secret values."""

    setup: BrokerApiSetup
    configured: bool
    missing_required_env_vars: tuple[str, ...]
    configured_optional_env_vars: tuple[str, ...]


@dataclass(frozen=True)
class BrokerApiCredentials:
    """Loaded secret values for code that later builds a broker client."""

    setup: BrokerApiSetup
    values: dict[str, str]


BROKER_API_SETUPS: dict[Broker, BrokerApiSetup] = {
    Broker.TRADING212: BrokerApiSetup(
        broker=Broker.TRADING212,
        display_name="Trading 212",
        required_env_vars=("TRADING212_API_KEY", "TRADING212_API_SECRET"),
        optional_env_vars=("TRADING212_BASE_URL",),
        default_base_url_env_var="TRADING212_BASE_URL",
        docs_url="https://t212public-api-docs.redoc.ly/",
        auth_note="Personal API key generated inside Trading 212.",
        execution_supported=True,
        safety_note="Use only for read/paper workflows until the project has an explicit execution gate.",
    ),
    Broker.INTERACTIVE_BROKERS: BrokerApiSetup(
        broker=Broker.INTERACTIVE_BROKERS,
        display_name="Interactive Brokers",
        required_env_vars=("IBKR_GATEWAY_BASE_URL",),
        optional_env_vars=("IBKR_ACCOUNT_ID",),
        default_base_url_env_var="IBKR_GATEWAY_BASE_URL",
        docs_url="https://interactivebrokers.github.io/cpwebapi/",
        auth_note=(
            "Client Portal API uses an authenticated local gateway/session; this project stores "
            "only the gateway URL and optional account id."
        ),
        execution_supported=True,
        safety_note="Keep the gateway in paper or read-only use until approval and execution controls exist.",
    ),
    Broker.ROBINHOOD: BrokerApiSetup(
        broker=Broker.ROBINHOOD,
        display_name="Robinhood",
        required_env_vars=("ROBINHOOD_API_KEY", "ROBINHOOD_PRIVATE_KEY"),
        optional_env_vars=("ROBINHOOD_BASE_URL",),
        default_base_url_env_var="ROBINHOOD_BASE_URL",
        docs_url="https://docs.robinhood.com/",
        auth_note=(
            "Official API access is limited by product/region. Treat this setup as opt-in "
            "for official Robinhood API credentials only, not unofficial scraping clients."
        ),
        execution_supported=False,
        safety_note="Disabled for execution in this project until the exact official API surface is approved.",
    ),
    Broker.IG_GROUP: BrokerApiSetup(
        broker=Broker.IG_GROUP,
        display_name="IG Group",
        required_env_vars=("IG_API_KEY", "IG_USERNAME", "IG_PASSWORD"),
        optional_env_vars=("IG_ACCOUNT_TYPE", "IG_BASE_URL"),
        default_base_url_env_var="IG_BASE_URL",
        docs_url="https://labs.ig.com/gettingstarted",
        auth_note="API key plus IG login credentials; demo/live environment must be selected explicitly.",
        execution_supported=True,
        safety_note="Prefer demo credentials while this engine remains analysis-only.",
    ),
    Broker.CAPITAL_COM: BrokerApiSetup(
        broker=Broker.CAPITAL_COM,
        display_name="Capital.com",
        required_env_vars=(
            "CAPITAL_COM_API_KEY",
            "CAPITAL_COM_IDENTIFIER",
            "CAPITAL_COM_API_PASSWORD",
        ),
        optional_env_vars=("CAPITAL_COM_BASE_URL",),
        default_base_url_env_var="CAPITAL_COM_BASE_URL",
        docs_url="https://open-api.capital.com/",
        auth_note="API key plus identifier and API-key password; session tokens are obtained at runtime.",
        execution_supported=True,
        safety_note="Use the demo base URL until trading approval and risk controls are implemented.",
    ),
    Broker.PLUS500: BrokerApiSetup(
        broker=Broker.PLUS500,
        display_name="Plus500",
        required_env_vars=(),
        optional_env_vars=(),
        default_base_url_env_var=None,
        docs_url="https://www.plus500.com/",
        auth_note="No generally available public retail trading API is configured here.",
        execution_supported=False,
        safety_note="Unsupported as an execution venue unless Plus500 grants an official API integration.",
    ),
}


BROKER_ALIASES: dict[str, Broker] = {
    "trading212": Broker.TRADING212,
    "trading_212": Broker.TRADING212,
    "trading 212": Broker.TRADING212,
    "interactivebroker": Broker.INTERACTIVE_BROKERS,
    "interactivebrokers": Broker.INTERACTIVE_BROKERS,
    "interactive_broker": Broker.INTERACTIVE_BROKERS,
    "interactive_brokers": Broker.INTERACTIVE_BROKERS,
    "ib": Broker.INTERACTIVE_BROKERS,
    "ibkr": Broker.INTERACTIVE_BROKERS,
    "robinhood": Broker.ROBINHOOD,
    "robinghood": Broker.ROBINHOOD,
    "ig": Broker.IG_GROUP,
    "ig_group": Broker.IG_GROUP,
    "ig group": Broker.IG_GROUP,
    "capital": Broker.CAPITAL_COM,
    "capital.com": Broker.CAPITAL_COM,
    "capital_com": Broker.CAPITAL_COM,
    "capital com": Broker.CAPITAL_COM,
    "plus500": Broker.PLUS500,
    "plus_500": Broker.PLUS500,
    "plus 500": Broker.PLUS500,
}


def normalize_broker(value: str | Broker) -> Broker:
    """Return the canonical broker enum for user-facing broker names."""
    if isinstance(value, Broker):
        return value

    normalized = value.strip().lower().replace("-", "_")
    broker = BROKER_ALIASES.get(normalized)
    if broker is None:
        supported = ", ".join(sorted(broker.value for broker in BROKER_API_SETUPS))
        raise ValueError(f"Unknown broker {value!r}. Supported brokers: {supported}")
    return broker


def get_broker_api_setup(broker: str | Broker) -> BrokerApiSetup:
    """Return static API setup metadata for a broker."""
    return BROKER_API_SETUPS[normalize_broker(broker)]


def broker_api_status(
    broker: str | Broker,
    environ: Mapping[str, str] | None = None,
) -> BrokerApiStatus:
    """Return whether the required environment variables are present."""
    setup = get_broker_api_setup(broker)
    env = os.environ if environ is None else environ
    missing = tuple(name for name in setup.required_env_vars if not env.get(name))
    configured_optional = tuple(name for name in setup.optional_env_vars if env.get(name))
    return BrokerApiStatus(
        setup=setup,
        configured=setup.execution_supported and not missing,
        missing_required_env_vars=missing,
        configured_optional_env_vars=configured_optional,
    )


def all_broker_api_statuses(
    environ: Mapping[str, str] | None = None,
) -> tuple[BrokerApiStatus, ...]:
    """Return readiness summaries for every configured broker setup."""
    return tuple(broker_api_status(broker, environ) for broker in BROKER_API_SETUPS)


def load_broker_api_credentials(
    broker: str | Broker,
    environ: Mapping[str, str] | None = None,
) -> BrokerApiCredentials:
    """Load required and optional broker API values from the environment.

    Raises:
        RuntimeError: if the broker has no supported public API setup here.
        ValueError: if required environment variables are missing.
    """
    status = broker_api_status(broker, environ)
    if not status.setup.required_env_vars:
        raise RuntimeError(status.setup.auth_note)
    if status.missing_required_env_vars:
        missing = ", ".join(status.missing_required_env_vars)
        raise ValueError(
            f"Missing required environment variables for {status.setup.display_name}: {missing}"
        )

    env = os.environ if environ is None else environ
    names = status.setup.required_env_vars + status.setup.optional_env_vars
    values = {name: env[name] for name in names if env.get(name)}
    return BrokerApiCredentials(setup=status.setup, values=values)
