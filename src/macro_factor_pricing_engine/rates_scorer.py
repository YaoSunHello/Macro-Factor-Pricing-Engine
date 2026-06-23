"""Rates scorer wired to the structured Treasury policy."""

from dataclasses import dataclass

from macro_factor_pricing_engine.regimes import CausalMechanism, RegimeProbabilities
from macro_factor_pricing_engine.treasury_policy import build_treasury_policy


@dataclass(frozen=True)
class RatesScores:
    """Block scores and fired triggers for the rates slice."""

    cycle_score: int
    valuation_score: int
    fiscal_veto: bool
    overlay_modifier: float
    composite_signal: str
    fired_triggers: tuple[str, ...]
    derived_metrics: dict[str, float | bool]


def _value(raw: dict[str, object], name: str) -> float | bool:
    observations = raw["observations"]
    return observations[name]["value"]  # type: ignore[index]


def score_rates_snapshot(
    raw: dict[str, object],
    regime_probabilities: RegimeProbabilities,
) -> RatesScores:
    """Score the committed rates snapshot.

    Derived metrics are computed here rather than in the data source.
    """
    policy = build_treasury_policy()
    del policy  # Structured policy is imported here to keep scorer tied to the policy module.

    policy_rate = float(_value(raw, "policy_rate_midpoint"))
    core_pce_yoy = float(_value(raw, "core_pce_yoy"))
    core_pce_3m_ann = float(_value(raw, "core_pce_3m_annualized"))
    gdpnow = float(_value(raw, "gdpnow"))
    ism = float(_value(raw, "ism_composite"))
    payrolls = float(_value(raw, "payrolls_3m_avg_thousands"))
    acm_tp = float(_value(raw, "acm_ten_year_term_premium"))
    real_10y = float(_value(raw, "ten_year_real_yield"))
    move = float(_value(raw, "move_index"))
    move_rising = bool(_value(raw, "move_rising"))
    bid_to_cover_z = float(_value(raw, "bid_to_cover_z_score"))
    falling_indirect = bool(_value(raw, "falling_indirect_bidder_share"))
    qt_active = bool(_value(raw, "qt_active"))
    coupon_share_rising = bool(_value(raw, "coupon_issuance_share_rising"))
    five_year_be = float(_value(raw, "five_year_breakeven"))
    stock_bond_corr = float(_value(raw, "stock_bond_correlation_60d"))
    positioning_z = float(_value(raw, "cftc_specs_positioning_z"))
    yield_above_50d = bool(_value(raw, "ten_year_yield_above_50d_ma"))
    yield_above_200d = bool(_value(raw, "ten_year_yield_above_200d_ma"))
    cds_widening_z = float(_value(raw, "sovereign_cds_widening_z"))
    fiscal_event_live = bool(_value(raw, "adverse_fiscal_event_live"))
    persistent_tails = bool(_value(raw, "persistent_auction_tails"))

    real_policy_rate = policy_rate - core_pce_yoy
    breakeven_gap_to_core_pce = five_year_be - core_pce_yoy

    triggers: list[str] = []

    growth_score = 0
    if ism < 48 or payrolls < 75 or gdpnow < 1.0:
        growth_score = 1
        triggers.append("growth_slowdown_bullish_duration")
    elif ism > 52 or payrolls > 150 or gdpnow > 2.5:
        growth_score = -1
        triggers.append("growth_strength_bearish_duration")

    inflation_score = 0
    if core_pce_3m_ann < core_pce_yoy:
        inflation_score = 1
        triggers.append("inflation_momentum_easing")
    elif core_pce_3m_ann > core_pce_yoy:
        inflation_score = -1
        triggers.append("inflation_reaccelerating")

    policy_score = 0
    if real_policy_rate > 1.0:
        policy_score = 1
        triggers.append("policy_clearly_restrictive")
    elif real_policy_rate < 0.0:
        policy_score = -1
        triggers.append("policy_not_restrictive")

    cycle_score = growth_score + inflation_score + policy_score

    term_premium_score = 0
    if acm_tp > 1.8:
        term_premium_score = 2
        triggers.append("term_premium_strongly_attractive")
    elif acm_tp > 1.4:
        term_premium_score = 1
        triggers.append("term_premium_above_median")
    elif acm_tp < 0.5:
        term_premium_score = -1
        triggers.append("term_premium_thin_cushion")
    else:
        triggers.append("term_premium_below_median")

    supply_score = 0
    if bid_to_cover_z < 0 or falling_indirect:
        supply_score -= 1
        triggers.append("auction_demand_soft")
    if qt_active and coupon_share_rising:
        supply_score -= 1
        triggers.append("qt_and_coupon_supply_pressure")

    move_score = 0
    if move < 90:
        move_score = 1
        triggers.append("rate_volatility_calm")
    elif move > 120 and move_rising:
        move_score = -1
        triggers.append("move_high_and_rising")

    real_yield_score = 0
    if real_10y > 2.5:
        real_yield_score = 1
        triggers.append("real_yield_attractive")
    elif real_10y < 1.0:
        real_yield_score = -1
        triggers.append("real_yield_expensive")

    positioning_score = 0
    if positioning_z < -1.0:
        positioning_score = 1
        triggers.append("specs_net_short")
    elif positioning_z > 1.0:
        positioning_score = -1
        triggers.append("specs_crowded_long")

    momentum_score = -1 if yield_above_50d and yield_above_200d else 0
    if momentum_score < 0:
        triggers.append("yield_momentum_against_duration")

    valuation_score = (
        term_premium_score
        + supply_score
        + move_score
        + real_yield_score
        + positioning_score
        + momentum_score
    )

    fiscal_veto = sum(
        (
            cds_widening_z > 1.0,
            persistent_tails,
            fiscal_event_live,
        )
    ) >= 2
    if fiscal_veto:
        triggers.append("fiscal_veto")

    overlay_modifier = 1.0
    if stock_bond_corr > 0.3:
        overlay_modifier = 0.5
        triggers.append("positive_stock_bond_correlation_halves_long_end_add")
    elif stock_bond_corr < -0.2:
        overlay_modifier = 1.25
        triggers.append("negative_stock_bond_correlation_supports_duration")

    if breakeven_gap_to_core_pce < -0.5 and core_pce_3m_ann >= core_pce_yoy:
        triggers.append("tips_breakeven_cheap_vs_realized")

    dominant = regime_probabilities.dominant_regime()
    if dominant.mechanism == CausalMechanism.DELIBERATE_POLICY_DISRUPTION:
        triggers.append("regime_deliberate_policy_disruption")

    composite_signal = "front_belly_overweight_long_end_underweight_tips_overweight"
    if valuation_score >= 2 and not fiscal_veto and cycle_score >= -1:
        composite_signal = "duration_overweight"
    elif valuation_score <= 0 or fiscal_veto:
        composite_signal = "long_end_underweight"

    return RatesScores(
        cycle_score=cycle_score,
        valuation_score=valuation_score,
        fiscal_veto=fiscal_veto,
        overlay_modifier=overlay_modifier,
        composite_signal=composite_signal,
        fired_triggers=tuple(triggers),
        derived_metrics={
            "real_policy_rate": round(real_policy_rate, 3),
            "breakeven_gap_to_core_pce": round(breakeven_gap_to_core_pce, 3),
            "stock_bond_correlation_60d": stock_bond_corr,
            "acm_ten_year_term_premium": acm_tp,
        },
    )
