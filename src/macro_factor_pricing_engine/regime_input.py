"""Manual regime input for the thin rates loop."""

from macro_factor_pricing_engine.regimes import (
    CausalMechanism,
    MacroState,
    RegimeProbabilities,
    get_regime,
)


STAGE_1_PLACEHOLDER = (
    "STAGE 1 PLACEHOLDER - regime classification from data is the priority "
    "unbuilt module; this function emits the same RegimeProbabilities interface "
    "a future classifier will emit."
)


def default_manual_regime_probabilities() -> RegimeProbabilities:
    """Return the current manually supplied regime probabilities."""
    primary = get_regime(
        MacroState.STAGFLATION,
        CausalMechanism.DELIBERATE_POLICY_DISRUPTION,
    )
    secondary = get_regime(
        MacroState.REFLATION,
        CausalMechanism.CYCLICAL_NO_ACUTE_MECHANISM,
    )
    tertiary = get_regime(
        MacroState.STAGFLATION,
        CausalMechanism.LEVERAGE_INSTITUTIONAL_BREAKDOWN,
    )
    return RegimeProbabilities(
        {
            primary: 0.75,
            secondary: 0.15,
            tertiary: 0.10,
        }
    )
