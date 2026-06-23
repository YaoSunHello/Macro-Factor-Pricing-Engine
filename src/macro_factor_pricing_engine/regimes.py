"""Macro mechanism and regime definitions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RegimeDefinition:
    """Observable macro regime and its expected asset-class behavior."""

    name: str
    growth: str
    inflation: str
    policy_liquidity: str
    risk_appetite: str
    causal_story: str
    leading_asset_classes: tuple[str, ...]
    lagging_asset_classes: tuple[str, ...]
    observable_triggers: tuple[str, ...]


MACRO_TRANSMISSION_LOGIC: dict[str, str] = {
    "growth": (
        "Growth strength drives earnings expectations, default risk, commodity demand, "
        "and the market's tolerance for cyclical assets."
    ),
    "inflation": (
        "Inflation changes real purchasing power and central-bank reaction functions, "
        "so it drives real yields, duration sensitivity, and demand for real assets."
    ),
    "policy_liquidity": (
        "Policy and liquidity affect discount rates, funding stress, credit spreads, "
        "and the relative appeal of cash versus risk assets."
    ),
    "risk_appetite": (
        "Risk appetite captures whether investors are being paid to own drawdown-prone "
        "assets or should prefer liquidity, quality, and defensive duration."
    ),
}


REGIME_DEFINITIONS: tuple[RegimeDefinition, ...] = (
    RegimeDefinition(
        name="goldilocks",
        growth="stable_or_improving",
        inflation="stable_or_easing",
        policy_liquidity="neutral_or_easing",
        risk_appetite="constructive",
        causal_story=(
            "Growth supports earnings while inflation and policy do not force a sharp "
            "rise in discount rates. Credit stress is contained, so risk assets can lead."
        ),
        leading_asset_classes=(
            "us_equities",
            "global_developed_equities",
            "emerging_market_equities",
            "high_yield_credit",
        ),
        lagging_asset_classes=("cash", "usd_proxy"),
        observable_triggers=(
            "growth_momentum_positive",
            "inflation_momentum_not_accelerating",
            "credit_spreads_stable_or_tightening",
            "yield_curve_not_signaling_policy_shock",
        ),
    ),
    RegimeDefinition(
        name="reflation",
        growth="improving",
        inflation="rising",
        policy_liquidity="neutral_to_tightening",
        risk_appetite="constructive_but_rate_sensitive",
        causal_story=(
            "Demand improves and nominal activity rises. Cyclical assets can work, "
            "but long-duration assets face pressure if yields rise faster than earnings."
        ),
        leading_asset_classes=(
            "us_equities",
            "global_developed_equities",
            "emerging_market_equities",
            "broad_commodities",
        ),
        lagging_asset_classes=("long_duration_government_bonds", "cash"),
        observable_triggers=(
            "growth_momentum_positive",
            "inflation_momentum_positive",
            "commodity_trend_positive",
            "nominal_yields_rising",
        ),
    ),
    RegimeDefinition(
        name="stagflation",
        growth="weakening",
        inflation="high_or_rising",
        policy_liquidity="constrained",
        risk_appetite="fragile",
        causal_story=(
            "Inflation pressure limits the central bank's ability to support weakening "
            "growth. Real assets and cash are preferred to equity and credit beta."
        ),
        leading_asset_classes=(
            "gold",
            "broad_commodities",
            "inflation_linked_bonds",
            "cash",
        ),
        lagging_asset_classes=(
            "us_equities",
            "global_developed_equities",
            "high_yield_credit",
            "long_duration_government_bonds",
        ),
        observable_triggers=(
            "growth_momentum_negative",
            "inflation_momentum_positive",
            "real_yields_rising_or_policy_tight",
            "credit_spreads_widening",
        ),
    ),
    RegimeDefinition(
        name="disinflationary_slowdown",
        growth="weakening",
        inflation="easing",
        policy_liquidity="easing_expected",
        risk_appetite="cautious",
        causal_story=(
            "Growth weakens, but falling inflation gives policy room to ease. Duration "
            "and quality bonds can lead while credit and equities need confirmation."
        ),
        leading_asset_classes=(
            "intermediate_duration_government_bonds",
            "long_duration_government_bonds",
            "investment_grade_credit",
        ),
        lagging_asset_classes=("high_yield_credit", "broad_commodities"),
        observable_triggers=(
            "growth_momentum_negative",
            "inflation_momentum_negative",
            "nominal_yields_falling",
            "policy_expectations_easing",
        ),
    ),
    RegimeDefinition(
        name="crisis_liquidity_stress",
        growth="shock_or_contraction",
        inflation="secondary",
        policy_liquidity="tight_or_disrupted",
        risk_appetite="risk_off",
        causal_story=(
            "Funding demand and drawdown control dominate. The strategy should protect "
            "capital with cash, government bonds, and USD exposure until stress fades."
        ),
        leading_asset_classes=(
            "cash",
            "short_duration_government_bonds",
            "long_duration_government_bonds",
            "usd_proxy",
        ),
        lagging_asset_classes=(
            "us_equities",
            "global_developed_equities",
            "emerging_market_equities",
            "high_yield_credit",
        ),
        observable_triggers=(
            "credit_spreads_widening_fast",
            "usd_trend_positive",
            "equity_drawdown_breach",
            "volatility_or_financial_conditions_stress",
        ),
    ),
    RegimeDefinition(
        name="policy_tightening_shock",
        growth="mixed_or_slowing",
        inflation="too_high",
        policy_liquidity="tightening_fast",
        risk_appetite="rate_shock",
        causal_story=(
            "Policy rates and real yields rise faster than growth expectations. The "
            "strategy should reduce duration and beta until policy pressure stabilizes."
        ),
        leading_asset_classes=("cash", "short_duration_government_bonds", "usd_proxy"),
        lagging_asset_classes=(
            "long_duration_government_bonds",
            "high_yield_credit",
            "us_equities",
        ),
        observable_triggers=(
            "front_end_yields_rising_fast",
            "real_yields_rising",
            "inflation_surprise_positive",
            "financial_conditions_tightening",
        ),
    ),
)


def regime_names() -> tuple[str, ...]:
    """Return available regime identifiers."""
    return tuple(regime.name for regime in REGIME_DEFINITIONS)
