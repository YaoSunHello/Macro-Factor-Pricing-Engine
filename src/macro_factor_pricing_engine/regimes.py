"""Two-axis macro regime definitions.

Macro state describes the growth/inflation/policy/risk environment. Causal
mechanism describes why that state exists. Asset behavior is treated as a
heuristic prior, not a fitted estimate, because comparable historical samples
are sparse.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from math import isclose
from types import MappingProxyType
from typing import Mapping


class MacroState(StrEnum):
    """Observable macro state axis."""

    GOLDILOCKS = "goldilocks"
    REFLATION = "reflation"
    STAGFLATION = "stagflation"
    DISINFLATIONARY_SLOWDOWN = "disinflationary_slowdown"


class CausalMechanism(StrEnum):
    """Causal mechanism axis."""

    PEG_OR_PROMISE_BREAK = "peg_or_promise_break"
    DELIBERATE_POLICY_DISRUPTION = "deliberate_policy_disruption"
    LEVERAGE_INSTITUTIONAL_BREAKDOWN = "leverage_institutional_breakdown"
    CYCLICAL_NO_ACUTE_MECHANISM = "cyclical_no_acute_mechanism"


MACRO_TRANSMISSION_CHANNELS: frozenset[str] = frozenset(
    {
        "growth",
        "inflation",
        "policy_liquidity",
        "risk_appetite",
        "fiscal_sovereign",
    }
)


MACRO_TRANSMISSION_LOGIC: Mapping[str, str] = MappingProxyType(
    {
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
        "fiscal_sovereign": (
            "Fiscal credibility and sovereign supply risk can move term premium and "
            "duration independently from cyclical policy expectations."
        ),
    }
)


@dataclass(frozen=True)
class AssetMapOverride:
    """Mechanism-specific override to a base state's asset prior."""

    asset_class: str
    position: str
    reason: str


@dataclass(frozen=True)
class Regime:
    """A meaningful macro state and causal mechanism pair."""

    state: MacroState
    mechanism: CausalMechanism
    causal_story: str
    leading_assets: tuple[str, ...]
    lagging_assets: tuple[str, ...]
    observable_trigger_names: tuple[str, ...]
    asset_map_overrides: tuple[AssetMapOverride, ...] = ()
    asset_priors_are_heuristic: bool = True

    @property
    def name(self) -> str:
        """Stable pair identifier."""
        return f"{self.state.value}__{self.mechanism.value}"

    @property
    def leading_asset_classes(self) -> tuple[str, ...]:
        """Backward-compatible alias."""
        return self.leading_assets

    @property
    def lagging_asset_classes(self) -> tuple[str, ...]:
        """Backward-compatible alias."""
        return self.lagging_assets

    @property
    def observable_triggers(self) -> tuple[str, ...]:
        """Backward-compatible alias."""
        return self.observable_trigger_names

    def asset_position(self, asset_class: str) -> str:
        """Return the heuristic prior position for an asset class."""
        for override in self.asset_map_overrides:
            if override.asset_class == asset_class:
                return override.position
        if asset_class in self.leading_assets:
            return "overweight"
        if asset_class in self.lagging_assets:
            return "underweight"
        return "neutral"


RegimeDefinition = Regime


@dataclass(frozen=True)
class ValuationOverlay:
    """Timing overlay owned outside the macro-to-asset regime map.

    This placeholder intentionally has no score. Valuation and positioning are
    overlays that gate entry timing; they are not macro transmission channels.
    """

    name: str = "valuation_positioning_overlay"
    purpose: str = "owned outside the macro-to-asset mapping; gates entry timing"
    scoring_implemented: bool = False


@dataclass(frozen=True)
class MacroStateProfile:
    """State-level structural descriptor separate from mechanism playbooks."""

    state: MacroState
    growth_direction: str
    inflation_direction: str
    typical_root_causes: tuple[str, ...]
    typical_drivers: tuple[str, ...]
    key_indicators: tuple[str, ...]


@dataclass(frozen=True)
class RegimeProbabilities:
    """Soft assignment across defined regimes."""

    weights: Mapping[Regime, float]
    tolerance: float = 1e-6

    def __post_init__(self) -> None:
        if not self.weights:
            raise ValueError("RegimeProbabilities requires at least one regime weight")
        if any(weight < 0 for weight in self.weights.values()):
            raise ValueError("Regime probabilities cannot be negative")
        total = sum(self.weights.values())
        if not isclose(total, 1.0, abs_tol=self.tolerance):
            raise ValueError(f"Regime probabilities must sum to 1.0, got {total:.8f}")

    def dominant_regime(self) -> Regime:
        """Return the regime with the largest probability mass."""
        return max(self.weights, key=lambda regime: self.weights[regime])

    def is_transition(self, threshold: float = 0.6) -> bool:
        """Flag a transition when no single regime holds enough probability mass."""
        return max(self.weights.values()) <= threshold


MACRO_STATE_PROFILES: Mapping[MacroState, MacroStateProfile] = MappingProxyType(
    {
        MacroState.GOLDILOCKS: MacroStateProfile(
            state=MacroState.GOLDILOCKS,
            growth_direction="stable_positive",
            inflation_direction="low",
            typical_root_causes=("productivity boom", "supply-side expansion"),
            typical_drivers=("tech adoption", "global trade expansion"),
            key_indicators=(
                "positive output gap closing without unit-labor-cost spikes",
            ),
        ),
        MacroState.REFLATION: MacroStateProfile(
            state=MacroState.REFLATION,
            growth_direction="accelerating",
            inflation_direction="rising",
            typical_root_causes=("cyclical demand-pull", "fiscal expansion"),
            typical_drivers=(
                "post-recession inventory rebuild",
                "infrastructure spend",
            ),
            key_indicators=("credit-creation velocity", "steepening yield curve"),
        ),
        MacroState.STAGFLATION: MacroStateProfile(
            state=MacroState.STAGFLATION,
            growth_direction="decelerating",
            inflation_direction="sticky_high",
            typical_root_causes=(
                "supply-side shock",
                "structural policy distortion",
            ),
            typical_drivers=(
                "energy blockades",
                "structural de-globalization",
            ),
            key_indicators=(
                "collapsing profit margins alongside rising input/commodity prices",
            ),
        ),
        MacroState.DISINFLATIONARY_SLOWDOWN: MacroStateProfile(
            state=MacroState.DISINFLATIONARY_SLOWDOWN,
            growth_direction="decelerating",
            inflation_direction="falling",
            typical_root_causes=(
                "cyclical demand exhaustion",
                "post-bubble deleveraging",
            ),
            typical_drivers=("end of credit cycle", "monetary policy biting"),
            key_indicators=(
                "rising inventory-to-sales ratio",
                "widening credit spreads",
            ),
        ),
    }
)


TRANSITION_TIME_STEP = "monthly"
TRANSITION_MATRIX_IS_HEURISTIC = True
TRANSITION_TIER_KEY = (
    "adjacent~0.15, diagonal~0.05, reversal~0.03, stay=1-sum(off-diagonals); "
    "economic asymmetries override tiers"
)

TRANSITION_MATRIX: Mapping[MacroState, Mapping[MacroState, float]] = MappingProxyType(
    {
        MacroState.GOLDILOCKS: MappingProxyType(
            {
                MacroState.GOLDILOCKS: 0.67,
                MacroState.REFLATION: 0.15,
                MacroState.STAGFLATION: 0.03,
                MacroState.DISINFLATIONARY_SLOWDOWN: 0.15,
            }
        ),
        MacroState.REFLATION: MappingProxyType(
            {
                MacroState.GOLDILOCKS: 0.10,
                MacroState.REFLATION: 0.70,
                MacroState.STAGFLATION: 0.15,
                MacroState.DISINFLATIONARY_SLOWDOWN: 0.05,
            }
        ),
        MacroState.STAGFLATION: MappingProxyType(
            {
                MacroState.GOLDILOCKS: 0.03,
                MacroState.REFLATION: 0.05,
                MacroState.STAGFLATION: 0.77,
                MacroState.DISINFLATIONARY_SLOWDOWN: 0.15,
            }
        ),
        MacroState.DISINFLATIONARY_SLOWDOWN: MappingProxyType(
            {
                MacroState.GOLDILOCKS: 0.15,
                MacroState.REFLATION: 0.03,
                MacroState.STAGFLATION: 0.02,
                MacroState.DISINFLATIONARY_SLOWDOWN: 0.80,
            }
        ),
    }
)

TRANSITION_MATRIX_NOTES: tuple[str, ...] = (
    "Slowdown is stickiest at 0.80; main escape is recovery to Goldilocks.",
    "Reflation to Stagflation is 0.15 versus Stagflation to Reflation at 0.05.",
)

MECHANISM_ROW_MODIFIERS: Mapping[CausalMechanism, Mapping[MacroState, float]] = MappingProxyType(
    {
        CausalMechanism.PEG_OR_PROMISE_BREAK: MappingProxyType({}),
        CausalMechanism.DELIBERATE_POLICY_DISRUPTION: MappingProxyType({}),
        CausalMechanism.LEVERAGE_INSTITUTIONAL_BREAKDOWN: MappingProxyType(
            {
                MacroState.DISINFLATIONARY_SLOWDOWN: 3.0,
            }
        ),
        CausalMechanism.CYCLICAL_NO_ACUTE_MECHANISM: MappingProxyType({}),
    }
)


REGIME_DEFINITIONS: tuple[Regime, ...] = (
    Regime(
        state=MacroState.GOLDILOCKS,
        mechanism=CausalMechanism.CYCLICAL_NO_ACUTE_MECHANISM,
        causal_story=(
            "Growth supports earnings while inflation and policy do not force a sharp "
            "rise in discount rates. Credit stress is contained, so risk assets can lead."
        ),
        leading_assets=(
            "us_equities",
            "global_developed_equities",
            "emerging_market_equities",
            "high_yield_credit",
        ),
        lagging_assets=("cash", "usd_proxy"),
        observable_trigger_names=(
            "growth_momentum_positive",
            "inflation_momentum_not_accelerating",
            "credit_spreads_stable_or_tightening",
            "yield_curve_not_signaling_policy_shock",
        ),
    ),
    Regime(
        state=MacroState.REFLATION,
        mechanism=CausalMechanism.CYCLICAL_NO_ACUTE_MECHANISM,
        causal_story=(
            "Demand improves and nominal activity rises. Cyclical assets can work, "
            "but long-duration assets face pressure if yields rise faster than earnings."
        ),
        leading_assets=(
            "us_equities",
            "global_developed_equities",
            "emerging_market_equities",
            "broad_commodities",
        ),
        lagging_assets=("long_duration_government_bonds", "cash"),
        observable_trigger_names=(
            "growth_momentum_positive",
            "inflation_momentum_positive",
            "commodity_trend_positive",
            "nominal_yields_rising",
        ),
    ),
    Regime(
        state=MacroState.STAGFLATION,
        mechanism=CausalMechanism.DELIBERATE_POLICY_DISRUPTION,
        causal_story=(
            "Inflation and policy disruption dominate weak growth. Term-premium and "
            "fiscal risk can overwhelm the usual recession duration bid."
        ),
        leading_assets=("gold", "broad_commodities", "inflation_linked_bonds", "cash"),
        lagging_assets=(
            "us_equities",
            "global_developed_equities",
            "high_yield_credit",
            "long_duration_government_bonds",
        ),
        observable_trigger_names=(
            "growth_momentum_negative",
            "inflation_momentum_positive",
            "front_end_yields_rising_fast",
            "fiscal_or_term_premium_stress",
        ),
        asset_map_overrides=(
            AssetMapOverride(
                asset_class="long_duration_government_bonds",
                position="strong_underweight",
                reason="Term-premium and fiscal risk dominate the recession hedge.",
            ),
        ),
    ),
    Regime(
        state=MacroState.STAGFLATION,
        mechanism=CausalMechanism.LEVERAGE_INSTITUTIONAL_BREAKDOWN,
        causal_story=(
            "Inflation is uncomfortable, but institutional or leverage stress turns "
            "the dominant mechanism into deleveraging and policy response risk."
        ),
        leading_assets=(
            "cash",
            "short_duration_government_bonds",
            "long_duration_government_bonds",
            "usd_proxy",
        ),
        lagging_assets=("us_equities", "emerging_market_equities", "high_yield_credit"),
        observable_trigger_names=(
            "growth_momentum_negative",
            "inflation_high_or_sticky",
            "credit_spreads_widening_fast",
            "volatility_or_financial_conditions_stress",
        ),
        asset_map_overrides=(
            AssetMapOverride(
                asset_class="long_duration_government_bonds",
                position="overweight",
                reason="Flight-to-quality can dominate once policy response is expected.",
            ),
        ),
    ),
    Regime(
        state=MacroState.DISINFLATIONARY_SLOWDOWN,
        mechanism=CausalMechanism.CYCLICAL_NO_ACUTE_MECHANISM,
        causal_story=(
            "Growth weakens, but falling inflation gives policy room to ease. Duration "
            "and quality bonds can lead while credit and equities need confirmation."
        ),
        leading_assets=(
            "intermediate_duration_government_bonds",
            "long_duration_government_bonds",
            "investment_grade_credit",
        ),
        lagging_assets=("high_yield_credit", "broad_commodities"),
        observable_trigger_names=(
            "growth_momentum_negative",
            "inflation_momentum_negative",
            "nominal_yields_falling",
            "policy_expectations_easing",
        ),
    ),
    Regime(
        state=MacroState.DISINFLATIONARY_SLOWDOWN,
        mechanism=CausalMechanism.PEG_OR_PROMISE_BREAK,
        causal_story=(
            "A peg, promise, or policy anchor breaks. The cracking sovereign or asset "
            "should be avoided while core liquidity and front-belly duration can rally. "
            "USER TO CONFIRM: re-homed into the slowdown quadrant."
        ),
        leading_assets=("cash", "short_duration_government_bonds", "usd_proxy"),
        lagging_assets=(
            "emerging_market_equities",
            "high_yield_credit",
            "broad_commodities",
        ),
        observable_trigger_names=(
            "currency_or_policy_anchor_break",
            "usd_trend_positive",
            "credit_spreads_widening_fast",
            "cross_market_contagion",
        ),
    ),
    Regime(
        state=MacroState.DISINFLATIONARY_SLOWDOWN,
        mechanism=CausalMechanism.LEVERAGE_INSTITUTIONAL_BREAKDOWN,
        causal_story=(
            "Funding demand and drawdown control dominate. The strategy should protect "
            "capital with cash, government bonds, and USD exposure until stress fades. "
            "USER TO CONFIRM: re-homed into the slowdown quadrant."
        ),
        leading_assets=(
            "cash",
            "short_duration_government_bonds",
            "long_duration_government_bonds",
            "usd_proxy",
        ),
        lagging_assets=(
            "us_equities",
            "global_developed_equities",
            "emerging_market_equities",
            "high_yield_credit",
        ),
        observable_trigger_names=(
            "credit_spreads_widening_fast",
            "usd_trend_positive",
            "equity_drawdown_breach",
            "volatility_or_financial_conditions_stress",
        ),
    ),
    Regime(
        state=MacroState.DISINFLATIONARY_SLOWDOWN,
        mechanism=CausalMechanism.DELIBERATE_POLICY_DISRUPTION,
        causal_story=(
            "Policy rates and real yields rise faster than growth expectations. The "
            "strategy should reduce duration and beta until policy pressure stabilizes. "
            "USER TO CONFIRM: re-homed into the slowdown quadrant."
        ),
        leading_assets=("cash", "short_duration_government_bonds", "usd_proxy"),
        lagging_assets=(
            "long_duration_government_bonds",
            "high_yield_credit",
            "us_equities",
        ),
        observable_trigger_names=(
            "front_end_yields_rising_fast",
            "real_yields_rising",
            "inflation_surprise_positive",
            "financial_conditions_tightening",
        ),
    ),
)


DEFINED_REGIME_PAIRS: frozenset[tuple[MacroState, CausalMechanism]] = frozenset(
    (regime.state, regime.mechanism) for regime in REGIME_DEFINITIONS
)


UNDEFINED_REGIME_PAIR_RATIONALE: Mapping[tuple[MacroState, CausalMechanism], str] = MappingProxyType(
    {
        (state, mechanism): "left undefined because the pair is not a distinct strategy playbook yet"
        for state in MacroState
        for mechanism in CausalMechanism
        if (state, mechanism) not in DEFINED_REGIME_PAIRS
    }
)


VALUATION_OVERLAY = ValuationOverlay()


def state_profile(state: MacroState) -> MacroStateProfile:
    """Return the structural profile for a macro state."""
    return MACRO_STATE_PROFILES[state]


def transition_row(from_state: MacroState) -> Mapping[MacroState, float]:
    """Return the base state-only transition row."""
    return TRANSITION_MATRIX[from_state]


def transition_prob(from_state: MacroState, to_state: MacroState) -> float:
    """Return the base transition probability from one state to another."""
    return TRANSITION_MATRIX[from_state][to_state]


def transition_row_for(
    from_state: MacroState,
    mechanism: CausalMechanism,
) -> Mapping[MacroState, float]:
    """Return a mechanism-conditioned transition row.

    Multipliers are applied to the base row and then renormalized.
    """
    base_row = TRANSITION_MATRIX[from_state]
    modifiers = MECHANISM_ROW_MODIFIERS[mechanism]
    adjusted = {
        state: probability * modifiers.get(state, 1.0)
        for state, probability in base_row.items()
    }
    total = sum(adjusted.values())
    return MappingProxyType(
        {state: probability / total for state, probability in adjusted.items()}
    )


def validate_transition_matrix() -> None:
    """Validate state-profile and transition-matrix structure."""
    expected_states = set(MacroState)
    if set(MACRO_STATE_PROFILES) != expected_states:
        raise ValueError("MACRO_STATE_PROFILES must cover every MacroState exactly")
    if set(TRANSITION_MATRIX) != expected_states:
        raise ValueError("TRANSITION_MATRIX rows must cover every MacroState exactly")

    for from_state, row in TRANSITION_MATRIX.items():
        if set(row) != expected_states:
            raise ValueError(f"Transition row for {from_state.value} has invalid keys")
        if any(probability < 0 for probability in row.values()):
            raise ValueError(f"Transition row for {from_state.value} has negative values")
        total = sum(row.values())
        if not isclose(total, 1.0, abs_tol=1e-9):
            raise ValueError(f"Transition row for {from_state.value} sums to {total}")

    if set(MECHANISM_ROW_MODIFIERS) != set(CausalMechanism):
        raise ValueError("MECHANISM_ROW_MODIFIERS must cover every CausalMechanism")


def regime_names() -> tuple[str, ...]:
    """Return available regime pair identifiers."""
    return tuple(regime.name for regime in REGIME_DEFINITIONS)


def get_regime(state: MacroState, mechanism: CausalMechanism) -> Regime:
    """Return a defined regime pair or raise for undefined combinations."""
    for regime in REGIME_DEFINITIONS:
        if regime.state == state and regime.mechanism == mechanism:
            return regime
    raise KeyError(f"Undefined regime pair: {state.value} x {mechanism.value}")


validate_transition_matrix()
