"""Read-only FastAPI seam for the local dashboard."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

try:  # Keep serialization helpers importable before web dependencies are installed.
    from fastapi import FastAPI
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles
except ModuleNotFoundError:  # pragma: no cover - exercised only in minimal envs.
    FastAPI = None  # type: ignore[assignment]
    FileResponse = None  # type: ignore[assignment]
    StaticFiles = None  # type: ignore[assignment]

from macro_factor_pricing_engine.app import Recommendation, run_analysis
from macro_factor_pricing_engine.regimes import (
    DEFINED_REGIME_PAIRS,
    CausalMechanism,
    MacroState,
    Regime,
)
from macro_factor_pricing_engine.universe import asset_classes


def _regime_payload(regime: Regime, weight: float) -> dict[str, Any]:
    return {
        "state": regime.state.value,
        "mechanism": regime.mechanism.value,
        "name": regime.name,
        "weight": weight,
        "causal_story": regime.causal_story,
        "leading_assets": list(regime.leading_assets),
        "lagging_assets": list(regime.lagging_assets),
    }


def serialize_recommendation(recommendation: Recommendation) -> dict[str, Any]:
    """Serialize an analysis recommendation for read-only frontend use."""
    regime_probabilities = recommendation.regime_probabilities
    dominant = regime_probabilities.dominant_regime()
    max_mass = max(regime_probabilities.weights.values())
    defined_pairs = sorted(
        (
            {"state": state.value, "mechanism": mechanism.value}
            for state, mechanism in DEFINED_REGIME_PAIRS
        ),
        key=lambda pair: (pair["state"], pair["mechanism"]),
    )

    return {
        "regime_distribution": [
            _regime_payload(regime, weight)
            for regime, weight in regime_probabilities.weights.items()
        ],
        "dominant": {
            "state": dominant.state.value,
            "mechanism": dominant.mechanism.value,
            "name": dominant.name,
        },
        "is_transition": regime_probabilities.is_transition(0.6),
        "max_mass": max_mass,
        "defined_pairs": defined_pairs,
        "macro_states": [state.value for state in MacroState],
        "causal_mechanisms": [mechanism.value for mechanism in CausalMechanism],
        "scores": {
            "cycle": recommendation.scores.cycle_score,
            "valuation": recommendation.scores.valuation_score,
            "fiscal_veto": recommendation.scores.fiscal_veto,
            "overlay_modifier": recommendation.scores.overlay_modifier,
            "composite": recommendation.scores.composite_signal,
            "fired_triggers": list(recommendation.scores.fired_triggers),
        },
        "target_weights": [
            {
                "ticker": weight.ticker,
                "bucket": weight.bucket,
                "weight": weight.weight,
            }
            for weight in recommendation.target.weights
        ],
        "asset_classes": list(asset_classes()),
    }


def state_payload() -> dict[str, Any]:
    """Run analysis with temporary runtime paths and return dashboard JSON."""
    with TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        recommendation = run_analysis(
            inventory_path=tmp_path / "inventory.json",
            turnover_log_path=tmp_path / "turnover_ledger.jsonl",
        )
    return serialize_recommendation(recommendation)


def create_app() -> Any:
    """Create the Phase 1 read-only FastAPI app."""
    if FastAPI is None or StaticFiles is None or FileResponse is None:
        raise RuntimeError("FastAPI is not installed. Install project dependencies first.")

    app = FastAPI(title="Macro Factor Pricing Engine", version="0.1.0")
    frontend_dir = Path(__file__).resolve().parents[2] / "frontend"

    @app.get("/api/state")
    def get_state() -> dict[str, Any]:
        return state_payload()

    if frontend_dir.exists():
        app.mount("/static", StaticFiles(directory=frontend_dir), name="frontend")

        @app.get("/")
        def index() -> FileResponse:
            return FileResponse(frontend_dir / "index.html")

    return app


app = create_app() if FastAPI is not None else None
