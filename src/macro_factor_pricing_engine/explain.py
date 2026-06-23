"""Plain-language explanations for pending recommendations."""

from macro_factor_pricing_engine.rates_scorer import RatesScores
from macro_factor_pricing_engine.regimes import RegimeProbabilities
from macro_factor_pricing_engine.risk import RiskReadout
from macro_factor_pricing_engine.sizing import TargetPortfolio


def explain_recommendation(
    regime_probabilities: RegimeProbabilities,
    scores: RatesScores,
    target: TargetPortfolio,
    risk: RiskReadout,
) -> str:
    """Return the recommendation explanation."""
    regime_lines = ", ".join(
        f"{regime.name}={weight:.0%}"
        for regime, weight in regime_probabilities.weights.items()
    )
    triggers = ", ".join(scores.fired_triggers)
    return (
        "PENDING analysis recommendation only. "
        f"Manual regime probabilities: {regime_lines}. "
        f"Cycle score is {scores.cycle_score}; valuation score is {scores.valuation_score}; "
        f"fiscal veto is {scores.fiscal_veto}; overlay modifier is {scores.overlay_modifier}. "
        f"Fired triggers: {triggers}. "
        f"Sizing rationale: {target.sizing_rationale} "
        f"Portfolio duration is {risk.portfolio_duration}, with DV01 "
        f"{risk.dv01_per_1mm_notional} per $1mm notional. "
        "No execution is allowed because recommendations are pending and no scoped "
        "security is approved for allocation."
    )
