"""Strategic overall-portfolio benchmark by investment horizon.

The benchmark is the neutral strategic asset allocation the engine tilts away
from. It is a measurement reference, not the live portfolio. Starter SAA
weights are USER TO CONFIRM: the horizon glide is the researched principle,
while exact weights remain policy choices.
"""

from __future__ import annotations

from macro_factor_pricing_engine.universe import asset_classes


HORIZONS: tuple[str, ...] = ("10y", "5y", "1y", "1q")

HORIZON_BENCHMARKS: dict[str, dict[str, float]] = {
    "10y": {
        "us_equities": 0.30,
        "global_developed_equities": 0.28,
        "emerging_market_equities": 0.12,
        "gold": 0.05,
        "broad_commodities": 0.05,
        "intermediate_duration_government_bonds": 0.08,
        "long_duration_government_bonds": 0.04,
        "investment_grade_credit": 0.05,
        "high_yield_credit": 0.03,
    },
    "5y": {
        "us_equities": 0.22,
        "global_developed_equities": 0.20,
        "emerging_market_equities": 0.08,
        "gold": 0.04,
        "broad_commodities": 0.03,
        "short_duration_government_bonds": 0.05,
        "intermediate_duration_government_bonds": 0.12,
        "long_duration_government_bonds": 0.05,
        "inflation_linked_bonds": 0.05,
        "investment_grade_credit": 0.08,
        "high_yield_credit": 0.03,
        "cash": 0.05,
    },
    "1y": {
        "us_equities": 0.12,
        "global_developed_equities": 0.09,
        "emerging_market_equities": 0.04,
        "gold": 0.05,
        "short_duration_government_bonds": 0.30,
        "intermediate_duration_government_bonds": 0.12,
        "inflation_linked_bonds": 0.05,
        "investment_grade_credit": 0.08,
        "cash": 0.15,
    },
    "1q": {
        "cash": 1.00,
    },
}


def horizons() -> tuple[str, ...]:
    """Return canonical benchmark horizons from longest to shortest."""
    return HORIZONS


def benchmark_for(horizon: str) -> dict[str, float]:
    """Return a copy of the full benchmark blend for a horizon."""
    return dict(HORIZON_BENCHMARKS[horizon])


def benchmark_weight(horizon: str, asset_class: str) -> float:
    """Return an asset-class benchmark weight, or 0.0 when omitted."""
    return HORIZON_BENCHMARKS[horizon].get(asset_class, 0.0)


def validate() -> None:
    """Validate horizon names, universe keys, and weight sums."""
    if tuple(HORIZON_BENCHMARKS) != HORIZONS:
        raise ValueError("HORIZON_BENCHMARKS keys must exactly match HORIZONS order")

    valid_asset_classes = set(asset_classes())
    for horizon, weights in HORIZON_BENCHMARKS.items():
        invalid = set(weights) - valid_asset_classes
        if invalid:
            names = ", ".join(sorted(invalid))
            raise ValueError(f"Invalid benchmark asset classes for {horizon}: {names}")

        total_weight = sum(weights.values())
        if abs(total_weight - 1.0) > 1e-9:
            raise ValueError(f"Benchmark weights for {horizon} sum to {total_weight}")


validate()
