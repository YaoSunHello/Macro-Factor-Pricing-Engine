"""First-pass rates risk readout."""

from dataclasses import dataclass

from macro_factor_pricing_engine.sizing import TargetPortfolio


@dataclass(frozen=True)
class RiskReadout:
    """Simple portfolio risk readout for the pending target."""

    portfolio_duration: float
    dv01_per_1mm_notional: float
    bucket_exposure: dict[str, float]
    concentration_cap: float
    cap_breaches: tuple[str, ...]


def compute_risk_readout(
    target: TargetPortfolio,
    concentration_cap: float = 0.50,
    notional: float = 1_000_000.0,
) -> RiskReadout:
    """Compute duration, DV01, and bucket concentration flags."""
    portfolio_duration = sum(
        weight.weight * weight.duration_proxy_years for weight in target.weights
    )
    bucket_exposure = target.bucket_weights()
    cap_breaches = tuple(
        bucket for bucket, exposure in bucket_exposure.items() if exposure > concentration_cap
    )
    return RiskReadout(
        portfolio_duration=round(portfolio_duration, 3),
        dv01_per_1mm_notional=round(portfolio_duration * notional * 0.0001, 2),
        bucket_exposure={bucket: round(exposure, 6) for bucket, exposure in bucket_exposure.items()},
        concentration_cap=concentration_cap,
        cap_breaches=cap_breaches,
    )
