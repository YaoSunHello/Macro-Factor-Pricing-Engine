"""Structured Treasury strategy signal policy.

This module codifies the policy in TreasuryPolicy.md as auditable data. It does
not implement live scoring, data ingestion, or trade sizing.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class TreasuryInput:
    """Required input series for a Treasury signal block."""

    name: str
    source: str
    frequency: str
    block: str


@dataclass(frozen=True)
class TreasuryRule:
    """A heuristic signal rule from the Treasury policy."""

    name: str
    bullish_duration_condition: str
    bearish_duration_condition: str
    block: str


@dataclass(frozen=True)
class TreasuryPositioningRule:
    """Segment-level positioning rule."""

    segment: str
    rule: str


@dataclass(frozen=True)
class TreasuryChecklist:
    """Trigger checklist for adding or reducing duration."""

    action: str
    required_count: int
    conditions: tuple[str, ...]


@dataclass(frozen=True)
class TreasuryPolicy:
    """Treasury strategy decision-support policy."""

    version: str
    owner: str
    status: str
    sign_convention: str
    conceptual_blocks: tuple[str, ...]
    inputs: tuple[TreasuryInput, ...]
    signal_rules: tuple[TreasuryRule, ...]
    fiscal_credibility_gate: tuple[str, ...]
    cross_asset_overlay: tuple[str, ...]
    regime_playbooks: tuple[TreasuryPositioningRule, ...]
    positioning_matrix: tuple[TreasuryPositioningRule, ...]
    checklists: tuple[TreasuryChecklist, ...]
    governance: tuple[str, ...]


def build_treasury_policy() -> TreasuryPolicy:
    """Return the current structured Treasury policy."""
    return TreasuryPolicy(
        version="0.2",
        owner="Investment Risk",
        status=(
            "Heuristic decision-support framework; not a binding mandate or "
            "investment advice. Every signal state is a prior requiring human judgment."
        ),
        sign_convention=(
            "Positive score is bullish duration; negative score is bearish duration."
        ),
        conceptual_blocks=(
            "expected_short_rate_path",
            "term_premium",
            "fiscal_credibility_gate",
            "valuation_technicals_positioning",
            "cross_asset_overlay",
        ),
        inputs=(
            TreasuryInput("policy_rate_effective", "FRED DFF", "daily", "expected_short_rate_path"),
            TreasuryInput("implied_policy_path", "CME FedWatch", "daily", "expected_short_rate_path"),
            TreasuryInput("treasury_yields", "FRED DGS2/DGS5/DGS10/DGS30", "daily", "expected_short_rate_path"),
            TreasuryInput("core_pce", "FRED PCEPILFE", "monthly", "expected_short_rate_path"),
            TreasuryInput("cpi", "FRED CPIAUCSL", "monthly", "expected_short_rate_path"),
            TreasuryInput("wages", "FRED ECIWAG", "quarterly", "expected_short_rate_path"),
            TreasuryInput("inflation_nowcast", "Cleveland Fed Nowcast", "daily", "expected_short_rate_path"),
            TreasuryInput("growth_nowcast", "Atlanta Fed GDPNow", "weekly", "expected_short_rate_path"),
            TreasuryInput("payrolls", "BLS PAYEMS", "monthly", "expected_short_rate_path"),
            TreasuryInput("jobless_claims", "BLS ICSA", "weekly", "expected_short_rate_path"),
            TreasuryInput("acm_10y_term_premium", "NY Fed ACMTP10", "daily", "term_premium"),
            TreasuryInput("ten_year_real_yield", "FRED DFII10", "daily", "valuation_technicals_positioning"),
            TreasuryInput("issuance_qra_tbac", "Treasury QRA/TBAC", "quarterly", "term_premium"),
            TreasuryInput("auction_demand", "Treasury auction results", "per_auction", "term_premium"),
            TreasuryInput("qt_pace", "Fed H.4.1", "weekly", "term_premium"),
            TreasuryInput("rate_volatility", "MOVE index", "daily", "term_premium"),
            TreasuryInput("breakevens", "FRED T5YIE/T10YIE", "daily", "valuation_technicals_positioning"),
            TreasuryInput("cftc_positioning", "CFTC CoT TY/FV/US", "weekly", "valuation_technicals_positioning"),
            TreasuryInput("stock_bond_correlation", "SPX vs 10y total return", "daily", "cross_asset_overlay"),
            TreasuryInput("risk_gauges", "VIX, IG/HY OAS, DXY", "daily", "cross_asset_overlay"),
        ),
        signal_rules=(
            TreasuryRule(
                name="growth",
                bullish_duration_condition="ISM composite < 48, payrolls 3m average < 75k, or GDPNow < 1.0%",
                bearish_duration_condition="ISM > 52, payrolls 3m average > 150k, or GDPNow > 2.5%",
                block="expected_short_rate_path",
            ),
            TreasuryRule(
                name="inflation_momentum",
                bullish_duration_condition="Core PCE 3m annualised below year-on-year and falling",
                bearish_duration_condition="Core PCE 3m annualised above year-on-year and rising",
                block="expected_short_rate_path",
            ),
            TreasuryRule(
                name="policy_stance",
                bullish_duration_condition="Real policy rate above +1.0%",
                bearish_duration_condition="Real policy rate below 0%",
                block="expected_short_rate_path",
            ),
            TreasuryRule(
                name="acm_term_premium_level",
                bullish_duration_condition="ACM 10y term premium above 1.4%, strong above 1.8%",
                bearish_duration_condition="ACM 10y term premium below 0.5%",
                block="term_premium",
            ),
            TreasuryRule(
                name="auction_supply_demand",
                bullish_duration_condition="Bid-to-cover above trailing same-tenor average with repeated stop-throughs",
                bearish_duration_condition="Bid-to-cover below trailing average or persistent tails with falling indirect share",
                block="term_premium",
            ),
            TreasuryRule(
                name="rate_volatility",
                bullish_duration_condition="MOVE below 90",
                bearish_duration_condition="MOVE above 120 and rising",
                block="term_premium",
            ),
            TreasuryRule(
                name="ten_year_real_yield",
                bullish_duration_condition="10y real yield above 2.5%",
                bearish_duration_condition="10y real yield below 1.0%",
                block="valuation_technicals_positioning",
            ),
            TreasuryRule(
                name="positioning",
                bullish_duration_condition="CFTC specs net short above 1 z-score",
                bearish_duration_condition="CFTC specs net long above 1 z-score",
                block="valuation_technicals_positioning",
            ),
        ),
        fiscal_credibility_gate=(
            "Fiscal-stress flag is true if at least two fiscal stress indicators trigger.",
            "When true, cap long-end duration at neutral-to-underweight regardless of term premium or valuation.",
            "Bias toward steepener when fiscal credibility is deteriorating.",
        ),
        cross_asset_overlay=(
            "Stock-bond 60d correlation above +0.3 halves any long-end duration add.",
            "Stock-bond 60d correlation below -0.2 allows long-end add to scale up.",
            "Acute risk-off supports front-belly flight-to-quality; do not fade automatically.",
        ),
        regime_playbooks=(
            TreasuryPositioningRule(
                "peg_or_promise_break",
                "Own core front-belly duration, avoid the cracking sovereign, watch contagion.",
            ),
            TreasuryPositioningRule(
                "deliberate_policy_disruption",
                "Underweight long end, prefer front-belly carry, steepener bias, TIPS if breakevens are cheap.",
            ),
            TreasuryPositioningRule(
                "leverage_institutional_breakdown",
                "Add duration into policy response; long end can behave as recession hedge.",
            ),
        ),
        positioning_matrix=(
            TreasuryPositioningRule(
                "front_belly_2_5y",
                "Default overweight when carry/roll is positive and cycle score is non-negative.",
            ),
            TreasuryPositioningRule(
                "long_end_10_30y",
                "Overweight only with valuation score >= +2, no fiscal veto, and cycle score >= -1.",
            ),
            TreasuryPositioningRule(
                "curve_5s30s",
                "Steepener when fiscal veto, supply risk, term-premium risk, or bull-steepening cycle is active.",
            ),
            TreasuryPositioningRule(
                "tips_breakeven",
                "Overweight 5y TIPS when breakevens are cheap versus realised inflation and inflation momentum is not falling.",
            ),
        ),
        checklists=(
            TreasuryChecklist(
                action="add_long_end_duration",
                required_count=3,
                conditions=(
                    "Core PCE prints sub-3% annualised for two consecutive months.",
                    "ACM term premium is above 1.4%, strong add above 1.8%.",
                    "Payrolls roll over or unemployment rises more than 0.3pp off lows.",
                    "Energy or supply shock fades and breakevens fall.",
                    "Market underprices Fed pivot versus deteriorating data.",
                    "10y real yield is above 2.5%.",
                    "Stock-bond correlation falls below +0.3.",
                ),
            ),
            TreasuryChecklist(
                action="reduce_long_end_duration",
                required_count=3,
                conditions=(
                    "Inflation re-accelerates.",
                    "ACM term premium is below 0.5% and rising.",
                    "Persistent auction tails or falling indirect bidder share.",
                    "Fiscal-stress flag is true.",
                    "MOVE is above 120 and rising.",
                    "Positive stock-bond correlation with risk-on momentum.",
                    "CFTC specs are crowded net-long above 1 z-score.",
                ),
            ),
        ),
        governance=(
            "Weekly signal refresh.",
            "Monthly full block review.",
            "Quarterly threshold recalibration against backtest output.",
            "Use as structured prior, not autopilot.",
        ),
    )
