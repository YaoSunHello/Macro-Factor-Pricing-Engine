"""One-command rates analysis loop.

Run with:
    PYTHONPATH=src python3 -m macro_factor_pricing_engine.app
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from macro_factor_pricing_engine.data import SnapshotSource
from macro_factor_pricing_engine.explain import explain_recommendation
from macro_factor_pricing_engine.inventory import append_turnover_log, load_inventory
from macro_factor_pricing_engine.rates_scorer import RatesScores, score_rates_snapshot
from macro_factor_pricing_engine.regime_input import (
    STAGE_1_PLACEHOLDER,
    default_manual_regime_probabilities,
)
from macro_factor_pricing_engine.regimes import RegimeProbabilities
from macro_factor_pricing_engine.risk import RiskReadout, compute_risk_readout
from macro_factor_pricing_engine.sizing import TargetPortfolio, size_rates_targets
from macro_factor_pricing_engine.universe import has_tradeable_instruments, rates_securities


@dataclass(frozen=True)
class Recommendation:
    """End-to-end pending recommendation output."""

    mode: str
    status: str
    as_of: date
    regime_probabilities: RegimeProbabilities
    scores: RatesScores
    target: TargetPortfolio
    risk: RiskReadout
    turnover_rows_appended: int
    explanation: str


def run_analysis(
    as_of: date = date(2026, 6, 18),
    inventory_path: Path = Path(".runtime/inventory.json"),
    turnover_log_path: Path = Path(".runtime/turnover_ledger.jsonl"),
) -> Recommendation:
    """Run the thin rates loop end-to-end."""
    raw = SnapshotSource().load_raw(as_of=as_of)
    regime_probabilities = default_manual_regime_probabilities()
    scores = score_rates_snapshot(raw, regime_probabilities)
    target = size_rates_targets(scores, regime_probabilities)
    inventory = load_inventory(inventory_path)
    dominant_regime = regime_probabilities.dominant_regime().name
    rows_appended = append_turnover_log(
        turnover_log_path,
        as_of,
        target,
        inventory,
        scores,
        dominant_regime,
    )
    risk = compute_risk_readout(target)
    explanation = explain_recommendation(regime_probabilities, scores, target, risk)
    return Recommendation(
        mode="analysis",
        status="PENDING",
        as_of=as_of,
        regime_probabilities=regime_probabilities,
        scores=scores,
        target=target,
        risk=risk,
        turnover_rows_appended=rows_appended,
        explanation=explanation,
    )


def format_recommendation(recommendation: Recommendation) -> str:
    """Format a recommendation for CLI output."""
    regime_lines = "\n".join(
        f"  - {regime.name}: {weight:.0%}"
        for regime, weight in recommendation.regime_probabilities.weights.items()
    )
    target_lines = "\n".join(
        f"  - {weight.ticker} ({weight.bucket}): {weight.weight:.2%}"
        for weight in recommendation.target.weights
    )
    bucket_lines = "\n".join(
        f"  - {bucket}: {exposure:.2%}"
        for bucket, exposure in recommendation.risk.bucket_exposure.items()
    )
    scoped = ", ".join(str(security["ticker"]) for security in rates_securities())
    trade_gate = "closed" if not has_tradeable_instruments() else "open"
    return "\n".join(
        (
            "Macro Factor Pricing Engine - Rates Analysis",
            f"Mode: {recommendation.mode}",
            f"Status: {recommendation.status}",
            f"As of: {recommendation.as_of.isoformat()}",
            f"Trade gate: {trade_gate}",
            "",
            STAGE_1_PLACEHOLDER,
            "",
            "Scoped rates securities:",
            f"  {scoped}",
            "",
            "Manual regime probabilities:",
            regime_lines,
            "",
            "Scores:",
            f"  Cycle: {recommendation.scores.cycle_score}",
            f"  Valuation: {recommendation.scores.valuation_score}",
            f"  Fiscal veto: {recommendation.scores.fiscal_veto}",
            f"  Overlay modifier: {recommendation.scores.overlay_modifier}",
            f"  Composite signal: {recommendation.scores.composite_signal}",
            f"  Fired triggers: {', '.join(recommendation.scores.fired_triggers)}",
            "",
            "Target portfolio:",
            target_lines,
            "",
            "Risk readout:",
            f"  Portfolio duration: {recommendation.risk.portfolio_duration}",
            f"  DV01 per $1mm notional: {recommendation.risk.dv01_per_1mm_notional}",
            f"  Concentration cap: {recommendation.risk.concentration_cap:.0%}",
            "  Bucket exposure:",
            bucket_lines,
            f"  Cap breaches: {recommendation.risk.cap_breaches or 'none'}",
            "",
            f"Turnover rows appended: {recommendation.turnover_rows_appended}",
            "",
            "Explanation:",
            recommendation.explanation,
        )
    )


def main() -> None:
    recommendation = run_analysis()
    print(format_recommendation(recommendation))


if __name__ == "__main__":
    main()
