"""Persistent paper inventory and append-only turnover ledger."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

from macro_factor_pricing_engine.rates_scorer import RatesScores
from macro_factor_pricing_engine.sizing import TargetPortfolio


@dataclass(frozen=True)
class InventoryPosition:
    """Current paper position."""

    ticker: str
    bucket: str
    weight: float
    duration_proxy_years: float


def load_inventory(path: Path) -> tuple[InventoryPosition, ...]:
    """Load a persistent inventory snapshot; missing file means blank portfolio."""
    if not path.exists():
        return ()
    payload = json.loads(path.read_text())
    return tuple(InventoryPosition(**position) for position in payload.get("positions", ()))


def current_weight_map(inventory: tuple[InventoryPosition, ...]) -> dict[str, float]:
    """Return current weights by ticker."""
    return {position.ticker: position.weight for position in inventory}


def append_turnover_log(
    path: Path,
    run_date: date,
    target: TargetPortfolio,
    inventory: tuple[InventoryPosition, ...],
    scores: RatesScores,
    regime_name: str,
) -> int:
    """Append recommended changes and return row count appended."""
    path.parent.mkdir(parents=True, exist_ok=True)
    current = current_weight_map(inventory)
    appended = 0
    with path.open("a") as handle:
        for weight in target.weights:
            from_weight = current.get(weight.ticker, 0.0)
            if round(from_weight, 6) == round(weight.weight, 6):
                continue
            row = {
                "date": run_date.isoformat(),
                "security": weight.ticker,
                "bucket": weight.bucket,
                "from_weight": from_weight,
                "to_weight": weight.weight,
                "composite_signal": scores.composite_signal,
                "fired_triggers": list(scores.fired_triggers),
                "regime": regime_name,
                "reason": weight.reason,
            }
            handle.write(json.dumps(row, sort_keys=True) + "\n")
            appended += 1
    return appended


def inventory_as_dicts(inventory: tuple[InventoryPosition, ...]) -> list[dict[str, object]]:
    """Return inventory rows for display."""
    return [asdict(position) for position in inventory]
