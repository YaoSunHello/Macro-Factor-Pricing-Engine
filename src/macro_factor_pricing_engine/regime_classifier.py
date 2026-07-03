"""Deterministic Stage 1 macro regime classifier."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Callable, Mapping

from macro_factor_pricing_engine.data.regime_indicator_schema import (
    REGIME_INDICATOR_FIELDS,
    RegimeIndicatorSnapshot,
)
from macro_factor_pricing_engine.regimes import (
    DEFINED_REGIME_PAIRS,
    MACRO_TRANSMISSION_CHANNELS,
    REGIME_DEFINITIONS,
    CausalMechanism,
    MacroState,
    Regime,
    RegimeProbabilities,
    get_regime,
)


UNIMPLEMENTED_TRIGGER_NAMES: frozenset[str] = frozenset(
    {
        "currency_or_policy_anchor_break",
        "cross_market_contagion",
        "real_yields_rising",
        "inflation_surprise_positive",
        "financial_conditions_tightening",
        "fiscal_or_term_premium_stress",
        "front_end_yields_rising_fast",
    }
)


@dataclass(frozen=True)
class ChannelScores:
    """Scores for the five macro transmission channels."""

    growth: float
    inflation: float
    policy_liquidity: float
    risk_appetite: float
    fiscal_sovereign: float

    def as_mapping(self) -> Mapping[str, float]:
        return MappingProxyType(
            {
                "growth": self.growth,
                "inflation": self.inflation,
                "policy_liquidity": self.policy_liquidity,
                "risk_appetite": self.risk_appetite,
                "fiscal_sovereign": self.fiscal_sovereign,
            }
        )


@dataclass(frozen=True)
class RegimeClassification:
    """Classifier output plus metadata that RegimeProbabilities cannot store."""

    probabilities: RegimeProbabilities
    channel_scores: ChannelScores
    observable_triggers: frozenset[str]
    missing_fields: frozenset[str]
    computed_state: MacroState
    computed_mechanism: CausalMechanism
    outside_defined_playbooks: bool = False
    override_audit: object | None = None

    @property
    def weights(self) -> Mapping[Regime, float]:
        return self.probabilities.weights

    def dominant_regime(self) -> Regime:
        return self.probabilities.dominant_regime()

    def is_transition(self, threshold: float = 0.6) -> bool:
        return self.probabilities.is_transition(threshold)


def _average(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _clip_score(value: float) -> float:
    return max(-1.0, min(1.0, value))


def _value_or_missing(value: float | None, fallback: float = 0.0) -> float:
    if value is None:
        return fallback
    return value


def acm_term_premium_channel_contribution(snapshot: RegimeIndicatorSnapshot) -> float:
    # USER TO CONFIRM: threshold not found in docs/market_history_patterns.md
    raise NotImplementedError("No doc-sourced ACM 10Y term-premium threshold is defined")


def _inflation_score(snapshot: RegimeIndicatorSnapshot) -> float:
    cpi = snapshot.cpi_yoy
    breakeven = snapshot.breakeven_5y5y

    # docs/market_history_patterns.md Part V Module B:
    # INFLATION_REGIME_HIGH: CPI > 4.5% OR 5Y5Y_Breakeven > 3.5%.
    if (cpi is not None and cpi > 4.5) or (breakeven is not None and breakeven > 3.5):
        return 1.0

    # docs/market_history_patterns.md Part V Module B:
    # INFLATION_REGIME_LOW: CPI < 2.5% AND 5Y5Y_Breakeven < 2.5%.
    if (
        cpi is not None
        and cpi < 2.5
        and (breakeven is None or breakeven < 2.5)
    ):
        return -1.0

    components: list[float] = []
    if cpi is not None:
        # docs/market_history_patterns.md Part V Module B: moderate band is CPI 2.5-4.5%.
        if cpi < 2.5:
            components.append(-0.5)
        elif cpi <= 4.5:
            components.append(0.5)
        else:
            components.append(1.0)
    if snapshot.core_cpi_yoy is not None:
        if snapshot.core_cpi_yoy < 2.5:
            components.append(-0.5)
        elif snapshot.core_cpi_yoy <= 4.5:
            components.append(0.5)
        else:
            components.append(1.0)
    if breakeven is not None:
        if breakeven < 2.5:
            components.append(-0.5)
        elif breakeven <= 3.5:
            components.append(0.5)
        else:
            components.append(1.0)
    return _clip_score(_average(components))


def _hy_oas_score(hy_oas: float | None) -> float:
    if hy_oas is None:
        return 0.0
    # docs/market_history_patterns.md Part V Module C plus README-required
    # graduated bands: <250 / 250-400 / 400-600 / 600-1000 / >1000 bp.
    if hy_oas < 250:
        return 1.0
    if hy_oas < 400:
        return 0.5
    if hy_oas < 600:
        return 0.0
    if hy_oas <= 1000:
        return -0.5
    return -1.0


def _vix_score(vix: float | None) -> float:
    if vix is None:
        return 0.0
    # docs/market_history_patterns.md Part V Module G:
    # VIX <15 / 15-25 / 25-35 / >35 / >60.
    if vix < 15:
        return 1.0
    if vix < 25:
        return 0.5
    if vix <= 35:
        return 0.0
    if vix <= 60:
        return -0.5
    return -1.0


def _growth_score(snapshot: RegimeIndicatorSnapshot) -> float:
    components: list[float] = []
    if snapshot.ism_manufacturing_pmi is not None:
        # docs/market_history_patterns.md Part V Module A:
        # RECESSION_SIGNAL_4: ISM_Manufacturing < 47.
        if snapshot.ism_manufacturing_pmi < 47:
            components.append(-1.0)
        else:
            components.append(0.5)
    if snapshot.chicago_fed_nai is not None:
        if snapshot.chicago_fed_nai > 0:
            components.append(0.5)
        elif snapshot.chicago_fed_nai < 0:
            components.append(-0.5)
        else:
            components.append(0.0)
    if snapshot.gdpnow_estimate is not None:
        if snapshot.gdpnow_estimate > 0:
            components.append(0.5)
        elif snapshot.gdpnow_estimate < 0:
            components.append(-0.5)
        else:
            components.append(0.0)
    return _clip_score(_average(components))


def _policy_liquidity_score(snapshot: RegimeIndicatorSnapshot) -> float:
    components: list[float] = []
    if snapshot.nfci is not None:
        # Chicago Fed NFCI methodology: zero is average financial conditions;
        # positive values are tighter than average, negative values looser.
        if snapshot.nfci > 0:
            components.append(-0.5)
        elif snapshot.nfci < 0:
            components.append(0.5)
        else:
            components.append(0.0)
    if snapshot.ust_2y_yield_chg_1m is not None:
        # Direction only; no doc-sourced fast/slow magnitude threshold is used.
        components.append(-0.25 if snapshot.ust_2y_yield_chg_1m > 0 else 0.25)
    if snapshot.ust_10y_yield_chg_1m is not None:
        # Direction only; no doc-sourced fast/slow magnitude threshold is used.
        components.append(-0.25 if snapshot.ust_10y_yield_chg_1m > 0 else 0.25)
    if snapshot.fed_funds_implied_path_chg_3m is not None:
        # Direction only; no doc-sourced fast/slow magnitude threshold is used.
        components.append(-0.25 if snapshot.fed_funds_implied_path_chg_3m > 0 else 0.25)
    return _clip_score(_average(components))


def _fiscal_sovereign_score(snapshot: RegimeIndicatorSnapshot) -> float:
    components: list[float] = []
    if snapshot.dxy_chg_3m is not None:
        # docs/market_history_patterns.md Part V Module E uses >5% over 6M.
        # Scaling assumption: a 3M change is annualized to a 6M equivalent by doubling.
        six_month_equivalent = snapshot.dxy_chg_3m * 2.0
        if six_month_equivalent > 5.0:
            components.append(-0.5)
        elif six_month_equivalent < -5.0:
            components.append(0.5)
        else:
            components.append(0.0)
    if snapshot.dxy_trend_direction is not None:
        components.append(-0.25 if snapshot.dxy_trend_direction > 0 else 0.25)
    return _clip_score(_average(components))


def compute_channel_scores(snapshot: RegimeIndicatorSnapshot) -> ChannelScores:
    """Compute deterministic [-1, 1] channel scores from sourced bands.

    Inflation maps Module B low/moderate/high bands to roughly -1.0/+0.5/+1.0.
    Risk appetite averages Module C HY OAS bands and Module G VIX bands as
    +1.0, +0.5, 0.0, -0.5, -1.0 from benign to crisis. Growth uses Module A's
    ISM <47 recession anchor as the negative extreme, with sign-only PMI/CFNAI/
    GDPNow direction for the remaining components. Policy/liquidity uses the
    Chicago Fed NFCI zero convention plus sign-only rates/fed-funds changes.
    Fiscal/sovereign uses Module E's >5% over 6M DXY threshold, scaled from the
    3M input by doubling; ACM term premium is intentionally left as a direct
    NotImplementedError stub because the threshold is absent from the doc.
    """
    channels = ChannelScores(
        growth=_growth_score(snapshot),
        inflation=_inflation_score(snapshot),
        policy_liquidity=_policy_liquidity_score(snapshot),
        risk_appetite=_clip_score(
            _average([_hy_oas_score(snapshot.hy_oas), _vix_score(snapshot.vix)])
        ),
        fiscal_sovereign=_fiscal_sovereign_score(snapshot),
    )
    if set(channels.as_mapping()) != set(MACRO_TRANSMISSION_CHANNELS):
        raise ValueError("ChannelScores must cover existing macro transmission channels")
    return channels


def trigger_currency_or_policy_anchor_break(snapshot: RegimeIndicatorSnapshot) -> bool:
    # USER TO CONFIRM: threshold not found in docs/market_history_patterns.md
    raise NotImplementedError("No doc-sourced threshold for currency_or_policy_anchor_break")


def trigger_cross_market_contagion(snapshot: RegimeIndicatorSnapshot) -> bool:
    # USER TO CONFIRM: threshold not found in docs/market_history_patterns.md
    raise NotImplementedError("No doc-sourced threshold for cross_market_contagion")


def trigger_real_yields_rising(snapshot: RegimeIndicatorSnapshot) -> bool:
    # USER TO CONFIRM: threshold not found in docs/market_history_patterns.md
    raise NotImplementedError("No doc-sourced threshold for real_yields_rising")


def trigger_inflation_surprise_positive(snapshot: RegimeIndicatorSnapshot) -> bool:
    # USER TO CONFIRM: threshold not found in docs/market_history_patterns.md
    raise NotImplementedError("No doc-sourced threshold for inflation_surprise_positive")


def trigger_financial_conditions_tightening(snapshot: RegimeIndicatorSnapshot) -> bool:
    # USER TO CONFIRM: threshold not found in docs/market_history_patterns.md
    raise NotImplementedError("No doc-sourced threshold for financial_conditions_tightening")


def trigger_fiscal_or_term_premium_stress(snapshot: RegimeIndicatorSnapshot) -> bool:
    # USER TO CONFIRM: threshold not found in docs/market_history_patterns.md
    raise NotImplementedError("No doc-sourced threshold for fiscal_or_term_premium_stress")


def trigger_front_end_yields_rising_fast(snapshot: RegimeIndicatorSnapshot) -> bool:
    # USER TO CONFIRM: threshold not found in docs/market_history_patterns.md
    raise NotImplementedError("No doc-sourced threshold for front_end_yields_rising_fast")


UNIMPLEMENTED_TRIGGER_STUBS: Mapping[str, Callable[[RegimeIndicatorSnapshot], bool]] = (
    MappingProxyType(
        {
            "currency_or_policy_anchor_break": trigger_currency_or_policy_anchor_break,
            "cross_market_contagion": trigger_cross_market_contagion,
            "real_yields_rising": trigger_real_yields_rising,
            "inflation_surprise_positive": trigger_inflation_surprise_positive,
            "financial_conditions_tightening": trigger_financial_conditions_tightening,
            "fiscal_or_term_premium_stress": trigger_fiscal_or_term_premium_stress,
            "front_end_yields_rising_fast": trigger_front_end_yields_rising_fast,
        }
    )
)


def derive_observable_triggers(
    scores: ChannelScores,
    snapshot: RegimeIndicatorSnapshot,
) -> frozenset[str]:
    """Map sourced conditions to trigger names already defined in regimes.py."""
    triggers: set[str] = set()

    if snapshot.ism_manufacturing_pmi is not None and snapshot.ism_manufacturing_pmi < 47:
        # docs/market_history_patterns.md Part V Module A: ISM_Manufacturing <47.
        triggers.add("growth_momentum_negative")
    elif scores.growth < -0.3:
        # USER TO CONFIRM: band edges are a judgment call, not sourced.
        triggers.add("growth_momentum_negative")
    elif scores.growth > 0.3:
        # USER TO CONFIRM: band edges are a judgment call, not sourced.
        triggers.add("growth_momentum_positive")

    if scores.inflation <= 0.3:
        # USER TO CONFIRM: band edge is a judgment call, not sourced.
        triggers.add("inflation_momentum_negative")
        triggers.add("inflation_momentum_not_accelerating")
    if scores.inflation > 0.3:
        # USER TO CONFIRM: band edge is a judgment call, not sourced.
        triggers.add("inflation_momentum_positive")
    if (snapshot.cpi_yoy is not None and snapshot.cpi_yoy > 4.5) or (
        snapshot.breakeven_5y5y is not None and snapshot.breakeven_5y5y > 3.5
    ):
        # docs/market_history_patterns.md Part V Module B:
        # INFLATION_REGIME_HIGH: CPI >4.5% OR 5Y5Y_Breakeven >3.5%.
        triggers.add("inflation_high_or_sticky")

    if snapshot.hy_oas is not None and snapshot.hy_oas > 600:
        # docs/market_history_patterns.md Part V Module C:
        # HY spread crossing 600bps = strong recession confirmation.
        triggers.add("credit_spreads_widening_fast")
    elif snapshot.hy_oas_chg_1m is not None and snapshot.hy_oas_chg_1m > 150:
        # USER TO CONFIRM: no doc-sourced 1-month fast-widening magnitude exists.
        triggers.add("credit_spreads_widening_fast")
    elif snapshot.hy_oas is not None and snapshot.hy_oas < 400:
        # docs/market_history_patterns.md Part V Module C: below stress range.
        triggers.add("credit_spreads_stable_or_tightening")

    if snapshot.vix is not None and snapshot.vix > 35:
        # docs/market_history_patterns.md Part V Module G: VIX >35 crisis territory.
        triggers.add("volatility_or_financial_conditions_stress")
    if snapshot.nfci is not None and snapshot.nfci > 0.5:
        # Chicago Fed NFCI documentation: positive values indicate tighter-than-average
        # financial conditions; +0.5 is a project threshold requiring owner review.
        triggers.add("volatility_or_financial_conditions_stress")

    if (
        snapshot.sp500_drawdown_from_52w_high is not None
        and snapshot.sp500_drawdown_from_52w_high > 20
    ):
        # docs/market_history_patterns.md Part IV: bear markets are >20% peak decline.
        triggers.add("equity_drawdown_breach")

    if snapshot.dxy_chg_3m is not None and snapshot.dxy_chg_3m * 2.0 > 5.0:
        # docs/market_history_patterns.md Part V Module E uses >5% over 6M.
        # Scaling assumption: 3M input is doubled to a 6M equivalent.
        triggers.add("usd_trend_positive")

    if snapshot.broad_commodity_index_chg_3m is not None and snapshot.broad_commodity_index_chg_3m > 0:
        triggers.add("commodity_trend_positive")
    if snapshot.ust_10y_yield_chg_1m is not None:
        if snapshot.ust_10y_yield_chg_1m > 0:
            triggers.add("nominal_yields_rising")
        elif snapshot.ust_10y_yield_chg_1m < 0:
            triggers.add("nominal_yields_falling")
    if snapshot.fed_funds_implied_path_chg_3m is not None and snapshot.fed_funds_implied_path_chg_3m < 0:
        triggers.add("policy_expectations_easing")
    if (
        _value_or_missing(snapshot.ust_2y_yield_chg_1m) <= 0
        and _value_or_missing(snapshot.ust_10y_yield_chg_1m) <= 0
    ):
        triggers.add("yield_curve_not_signaling_policy_shock")

    defined_trigger_names = {
        trigger_name
        for regime in REGIME_DEFINITIONS
        for trigger_name in regime.observable_trigger_names
    }
    return frozenset(trigger for trigger in triggers if trigger in defined_trigger_names)


def _state_from_scores(scores: ChannelScores) -> MacroState:
    # USER TO CONFIRM: band edges are a judgment call, not sourced.
    growth_decelerating = scores.growth < -0.3
    growth_accelerating_or_stable = not growth_decelerating
    inflation_rising_or_sticky = scores.inflation > 0.3

    if growth_decelerating and inflation_rising_or_sticky:
        return MacroState.STAGFLATION
    if growth_decelerating and not inflation_rising_or_sticky:
        return MacroState.DISINFLATIONARY_SLOWDOWN
    if growth_accelerating_or_stable and inflation_rising_or_sticky:
        return MacroState.REFLATION
    return MacroState.GOLDILOCKS


def _mechanism_from_triggers(triggers: frozenset[str]) -> CausalMechanism:
    """Classify causal mechanism using an ordered hard-rule chain.

    First match wins. ``currency_or_policy_anchor_break`` is checked before
    overlapping stress triggers because it uniquely identifies peg/promise-break
    cases. Leverage/institutional breakdown then uses only its unique stress and
    drawdown triggers, not shared spread/USD triggers. Deliberate policy disruption
    requires at least two policy/real-yield/fiscal/inflation-tightening triggers
    because any single one can appear in ordinary cyclical markets. The mechanism
    axis is intentionally not blended into channel scores because it is a causal
    attribution rather than a magnitude scale.
    """
    if "currency_or_policy_anchor_break" in triggers:
        return CausalMechanism.PEG_OR_PROMISE_BREAK
    if (
        "volatility_or_financial_conditions_stress" in triggers
        or "equity_drawdown_breach" in triggers
    ):
        return CausalMechanism.LEVERAGE_INSTITUTIONAL_BREAKDOWN

    policy_disruption_triggers = {
        "front_end_yields_rising_fast",
        "real_yields_rising",
        "fiscal_or_term_premium_stress",
        "inflation_surprise_positive",
        "financial_conditions_tightening",
    }
    if len(policy_disruption_triggers.intersection(triggers)) >= 2:
        return CausalMechanism.DELIBERATE_POLICY_DISRUPTION
    return CausalMechanism.CYCLICAL_NO_ACUTE_MECHANISM


def _classification_confidence(snapshot: RegimeIndicatorSnapshot) -> float:
    missing_ratio = len(snapshot.missing_fields) / len(REGIME_INDICATOR_FIELDS)
    return max(0.35, min(0.78, 0.78 - missing_ratio * 0.45))


def _defined_regimes_for(state: MacroState | None = None) -> tuple[Regime, ...]:
    regimes = tuple(
        regime for regime in REGIME_DEFINITIONS if state is None or regime.state == state
    )
    if not regimes:
        return REGIME_DEFINITIONS
    return regimes


def _spread_residual(
    weights: dict[Regime, float],
    residual: float,
    excluded: set[Regime],
) -> dict[Regime, float]:
    recipients = [regime for regime in REGIME_DEFINITIONS if regime not in excluded]
    if not recipients:
        return weights
    share = residual / len(recipients)
    for regime in recipients:
        weights[regime] = weights.get(regime, 0.0) + share
    return weights


def _probabilities_for_defined_pair(
    state: MacroState,
    mechanism: CausalMechanism,
    confidence: float,
) -> RegimeProbabilities:
    primary = get_regime(state, mechanism)
    weights: dict[Regime, float] = {primary: confidence}
    excluded = {primary}

    same_mechanism = [
        regime
        for regime in REGIME_DEFINITIONS
        if regime.mechanism == mechanism and regime != primary
    ]
    mechanism_reserve = min(0.15, 1.0 - confidence)
    if same_mechanism and mechanism_reserve > 0:
        share = mechanism_reserve / len(same_mechanism)
        for regime in same_mechanism:
            weights[regime] = share
            excluded.add(regime)

    return RegimeProbabilities(
        _spread_residual(weights, 1.0 - sum(weights.values()), excluded)
    )


def _probabilities_for_undefined_pair(state: MacroState) -> RegimeProbabilities:
    fallback_regimes = _defined_regimes_for(state)
    share = 1.0 / len(fallback_regimes)
    return RegimeProbabilities({regime: share for regime in fallback_regimes})


def classify_regime(snapshot: RegimeIndicatorSnapshot) -> RegimeClassification:
    """Classify a raw snapshot into regime probabilities and review metadata."""
    scores = compute_channel_scores(snapshot)
    triggers = derive_observable_triggers(scores, snapshot)
    state = _state_from_scores(scores)
    mechanism = _mechanism_from_triggers(triggers)

    if (state, mechanism) in DEFINED_REGIME_PAIRS:
        probabilities = _probabilities_for_defined_pair(
            state,
            mechanism,
            _classification_confidence(snapshot),
        )
        outside_defined_playbooks = False
    else:
        probabilities = _probabilities_for_undefined_pair(state)
        outside_defined_playbooks = True

    return RegimeClassification(
        probabilities=probabilities,
        channel_scores=scores,
        observable_triggers=triggers,
        missing_fields=snapshot.missing_fields,
        computed_state=state,
        computed_mechanism=mechanism,
        outside_defined_playbooks=outside_defined_playbooks,
    )
