"""Pluggable data sources for analysis snapshots."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from importlib import resources
from typing import Protocol


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
