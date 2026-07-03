"""Pluggable data sources for analysis snapshots."""

from __future__ import annotations

import json
import csv
from dataclasses import dataclass
from datetime import date, timedelta
from importlib import resources
from io import StringIO
from typing import Protocol
from urllib.error import URLError
from urllib.request import urlopen


class DataSource(Protocol):
    """Raw data source that enforces point-in-time access."""

    def load_raw(self, as_of: date) -> dict[str, object]:
        """Return raw observations available on or before as_of."""


@dataclass(frozen=True)
class SnapshotSource:
    """Read a committed raw fixture and enforce no-lookahead by date."""

    fixture_name: str = "snapshot_2026_06_18.json"

    def load_raw(self, as_of: date) -> dict[str, object]:
        with resources.files("macro_factor_pricing_engine.data").joinpath(self.fixture_name).open() as handle:
            payload = json.load(handle)

        observations = payload["observations"]
        leaked = [
            name
            for name, observation in observations.items()
            if date.fromisoformat(observation["date"]) > as_of
        ]
        if leaked:
            raise ValueError(f"Snapshot contains observations after {as_of}: {leaked}")

        return {
            "snapshot_name": payload["snapshot_name"],
            "as_of": payload["as_of"],
            "observations": observations,
        }


@dataclass(frozen=True)
class FredSource:
    """Future FRED-backed source behind the same interface.

    This is intentionally allowed-missing for now; live data wiring is out of
    scope for the thin rates loop.
    """

    allow_missing: bool = True

    def load_raw(self, as_of: date) -> dict[str, object]:
        return {
            "snapshot_name": "fred_stub",
            "as_of": as_of.isoformat(),
            "observations": {},
            "allowed_missing": self.allow_missing,
        }


def _fred_csv_rows(series_id: str, as_of: date) -> list[tuple[date, float]]:
    url = (
        "https://fred.stlouisfed.org/graph/fredgraph.csv"
        f"?id={series_id}&observation_end={as_of.isoformat()}"
    )
    try:
        with urlopen(url, timeout=10) as response:
            payload = response.read().decode("utf-8")
    except (OSError, URLError):
        return []

    rows: list[tuple[date, float]] = []
    for row in csv.DictReader(StringIO(payload)):
        raw_value = row.get(series_id)
        if not raw_value or raw_value == ".":
            continue
        observed_at = date.fromisoformat(row["observation_date"])
        if observed_at <= as_of:
            rows.append((observed_at, float(raw_value)))
    return rows


def _fred_latest(series_id: str, as_of: date) -> tuple[float | None, date]:
    rows = _fred_csv_rows(series_id, as_of)
    if not rows:
        return None, as_of
    return rows[-1][1], rows[-1][0]


def _fred_change(series_id: str, as_of: date, lookback_days: int) -> tuple[float | None, date]:
    rows = _fred_csv_rows(series_id, as_of)
    if not rows:
        return None, as_of

    current_date, current_value = rows[-1]
    cutoff = current_date - timedelta(days=lookback_days)
    prior_candidates = [row for row in rows if row[0] <= cutoff]
    if not prior_candidates:
        return None, current_date
    return current_value - prior_candidates[-1][1], current_date


def _fred_pct_change(series_id: str, as_of: date, lookback_days: int) -> tuple[float | None, date]:
    rows = _fred_csv_rows(series_id, as_of)
    if not rows:
        return None, as_of

    current_date, current_value = rows[-1]
    cutoff = current_date - timedelta(days=lookback_days)
    prior_candidates = [row for row in rows if row[0] <= cutoff]
    if not prior_candidates:
        return None, current_date
    prior_value = prior_candidates[-1][1]
    if prior_value == 0:
        return None, current_date
    return (current_value / prior_value - 1.0) * 100.0, current_date


def fetch_ism_manufacturing_pmi(as_of: date) -> tuple[float | None, date]:
    return _fred_latest("NAPM", as_of)


def fetch_chicago_fed_nai(as_of: date) -> tuple[float | None, date]:
    return _fred_latest("CFNAI", as_of)


def fetch_gdpnow_estimate(as_of: date) -> tuple[float | None, date]:
    return _fred_latest("GDPNOW", as_of)


def fetch_cpi_yoy(as_of: date) -> tuple[float | None, date]:
    return _fred_pct_change("CPIAUCSL", as_of, 365)


def fetch_core_cpi_yoy(as_of: date) -> tuple[float | None, date]:
    return _fred_pct_change("CPILFESL", as_of, 365)


def fetch_breakeven_5y5y(as_of: date) -> tuple[float | None, date]:
    return _fred_latest("T5YIFR", as_of)


def fetch_ust_2y_yield(as_of: date) -> tuple[float | None, date]:
    return _fred_latest("DGS2", as_of)


def fetch_ust_2y_yield_chg_1m(as_of: date) -> tuple[float | None, date]:
    return _fred_change("DGS2", as_of, 30)


def fetch_ust_10y_yield(as_of: date) -> tuple[float | None, date]:
    return _fred_latest("DGS10", as_of)


def fetch_ust_10y_yield_chg_1m(as_of: date) -> tuple[float | None, date]:
    return _fred_change("DGS10", as_of, 30)


def fetch_fed_funds_implied_path_chg_3m(as_of: date) -> tuple[float | None, date]:
    return _fred_change("FEDFUNDS", as_of, 90)


def fetch_nfci(as_of: date) -> tuple[float | None, date]:
    return _fred_latest("NFCI", as_of)


def fetch_ig_oas(as_of: date) -> tuple[float | None, date]:
    value, observed_at = _fred_latest("BAMLC0A0CM", as_of)
    return (None if value is None else value * 100.0), observed_at


def fetch_ig_oas_chg_1m(as_of: date) -> tuple[float | None, date]:
    value, observed_at = _fred_change("BAMLC0A0CM", as_of, 30)
    return (None if value is None else value * 100.0), observed_at


def fetch_hy_oas(as_of: date) -> tuple[float | None, date]:
    value, observed_at = _fred_latest("BAMLH0A0HYM2", as_of)
    return (None if value is None else value * 100.0), observed_at


def fetch_hy_oas_chg_1m(as_of: date) -> tuple[float | None, date]:
    value, observed_at = _fred_change("BAMLH0A0HYM2", as_of, 30)
    return (None if value is None else value * 100.0), observed_at


def fetch_vix(as_of: date) -> tuple[float | None, date]:
    return _fred_latest("VIXCLS", as_of)


def fetch_acm_term_premium_10y(as_of: date) -> tuple[float | None, date]:
    return _fred_latest("THREEFYTP10", as_of)


def fetch_dxy_chg_3m(as_of: date) -> tuple[float | None, date]:
    return _fred_pct_change("DTWEXBGS", as_of, 90)


def fetch_dxy_trend_direction(as_of: date) -> tuple[float | None, date]:
    change, observed_at = fetch_dxy_chg_3m(as_of)
    if change is None:
        return None, observed_at
    if change > 0:
        return 1.0, observed_at
    if change < 0:
        return -1.0, observed_at
    return 0.0, observed_at


def fetch_broad_commodity_index_chg_3m(as_of: date) -> tuple[float | None, date]:
    return _fred_pct_change("PALLFNFINDEXQ", as_of, 90)


def fetch_sp500_drawdown_from_52w_high(as_of: date) -> tuple[float | None, date]:
    rows = _fred_csv_rows("SP500", as_of)
    if not rows:
        return None, as_of
    current_date, current_value = rows[-1]
    lookback_start = current_date - timedelta(days=365)
    trailing_values = [value for observed_at, value in rows if observed_at >= lookback_start]
    if not trailing_values:
        return None, current_date
    peak = max(trailing_values)
    if peak <= 0:
        return None, current_date
    return (peak - current_value) / peak * 100.0, current_date
