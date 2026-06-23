"""First-pass rates sizing convention."""

from dataclasses import dataclass

from macro_factor_pricing_engine.rates_scorer import RatesScores
from macro_factor_pricing_engine.regimes import CausalMechanism, RegimeProbabilities
from macro_factor_pricing_engine.universe import rates_securities


@dataclass(frozen=True)
class TargetWeight:
    """Target weight for an in-scope security."""

    ticker: str
    bucket: str
    weight: float
    duration_proxy_years: float
    approved_for_allocation: bool
    reason: str


@dataclass(frozen=True)
class TargetPortfolio:
    """Pending target portfolio from the thin rates loop."""

    weights: tuple[TargetWeight, ...]
    curve_trade_notes: tuple[str, ...]
    sizing_rationale: str

    def total_weight(self) -> float:
        return round(sum(weight.weight for weight in self.weights), 10)

    def bucket_weights(self) -> dict[str, float]:
        exposures: dict[str, float] = {}
        for weight in self.weights:
            exposures[weight.bucket] = exposures.get(weight.bucket, 0.0) + weight.weight
        return exposures


def _split_bucket_weight(bucket: str, bucket_weight: float) -> list[TargetWeight]:
    securities = [security for security in rates_securities() if security["bucket"] == bucket]
    if not securities:
        return []

    per_security = bucket_weight / len(securities)
    return [
        TargetWeight(
            ticker=str(security["ticker"]),
            bucket=bucket,
            weight=round(per_security, 6),
            duration_proxy_years=float(security["duration_proxy_years"]),
            approved_for_allocation=bool(security["approved_for_allocation"]),
            reason=str(security["role"]),
        )
        for security in securities
    ]


def size_rates_targets(
    scores: RatesScores,
    regime_probabilities: RegimeProbabilities,
) -> TargetPortfolio:
    """Translate rates scores into pending target weights."""
    dominant = regime_probabilities.dominant_regime()

    bucket_weights = {
        "short_duration_government_bonds": 0.25,
        "intermediate_duration_government_bonds": 0.25,
        "long_duration_government_bonds": 0.25,
        "inflation_linked_bonds": 0.25,
    }
    rationale = "Neutral starter allocation across in-scope rates buckets."

    if dominant.mechanism == CausalMechanism.DELIBERATE_POLICY_DISRUPTION:
        bucket_weights = {
            "short_duration_government_bonds": 0.25,
            "intermediate_duration_government_bonds": 0.40,
            "long_duration_government_bonds": 0.05,
            "inflation_linked_bonds": 0.30,
        }
        rationale = (
            "Deliberate policy disruption plus weak valuation score: overweight "
            "front-belly carry, underweight long-end term-premium risk, overweight TIPS."
        )

    if scores.fiscal_veto:
        bucket_weights["long_duration_government_bonds"] = min(
            bucket_weights["long_duration_government_bonds"],
            0.05,
        )

    weights: list[TargetWeight] = []
    for bucket, bucket_weight in bucket_weights.items():
        weights.extend(_split_bucket_weight(bucket, bucket_weight))

    rounding_gap = round(1.0 - sum(weight.weight for weight in weights), 6)
    if weights and rounding_gap:
        last = weights[-1]
        weights[-1] = TargetWeight(
            ticker=last.ticker,
            bucket=last.bucket,
            weight=round(last.weight + rounding_gap, 6),
            duration_proxy_years=last.duration_proxy_years,
            approved_for_allocation=last.approved_for_allocation,
            reason=last.reason,
        )

    return TargetPortfolio(
        weights=tuple(weights),
        curve_trade_notes=(
            "5s30s steepener bias is a relative trade note only; not forced into weights.",
        ),
        sizing_rationale=rationale,
    )
