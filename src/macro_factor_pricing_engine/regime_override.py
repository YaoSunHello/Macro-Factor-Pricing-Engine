"""Human-confirmed macro regime overrides."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from macro_factor_pricing_engine.policy import build_default_policy
from macro_factor_pricing_engine.regime_classifier import (
    ChannelScores,
    RegimeClassification,
)
from macro_factor_pricing_engine.regimes import (
    CausalMechanism,
    MacroState,
    RegimeProbabilities,
    get_regime,
)


@dataclass(frozen=True)
class RegimeOverride:
    """Structured human override of the computed two-axis regime."""

    state: MacroState
    mechanism: CausalMechanism
    confidence: float
    reason: str
    entered_by: str
    entered_at: datetime
    expires_at: datetime | None


@dataclass(frozen=True)
class RegimeOverrideAudit:
    """Audit trail comparing data-classified output with the override."""

    computed: RegimeProbabilities
    override: RegimeOverride
    policy_trigger_name: str
    requires_confirmation: bool


def _as_classification(computed: RegimeProbabilities | RegimeClassification) -> RegimeClassification:
    if isinstance(computed, RegimeClassification):
        return computed
    dominant = computed.dominant_regime()
    return RegimeClassification(
        probabilities=computed,
        channel_scores=ChannelScores(
            growth=0.0,
            inflation=0.0,
            policy_liquidity=0.0,
            risk_appetite=0.0,
            fiscal_sovereign=0.0,
        ),
        observable_triggers=frozenset(),
        missing_fields=frozenset(),
        computed_state=dominant.state,
        computed_mechanism=dominant.mechanism,
    )


def apply_override(
    computed: RegimeProbabilities | RegimeClassification,
    override: RegimeOverride | None,
) -> RegimeClassification:
    """Apply a human override after checking the policy confirmation trigger."""
    classification = _as_classification(computed)
    if override is None:
        return classification

    policy = build_default_policy()
    human_input_trigger = next(
        trigger for trigger in policy.triggers if trigger.name == "human_input_pending"
    )
    regime = get_regime(override.state, override.mechanism)
    probabilities = RegimeProbabilities({regime: 1.0})
    audit = RegimeOverrideAudit(
        computed=classification.probabilities,
        override=override,
        policy_trigger_name=human_input_trigger.name,
        requires_confirmation=human_input_trigger.requires_confirmation,
    )
    return RegimeClassification(
        probabilities=probabilities,
        channel_scores=classification.channel_scores,
        observable_triggers=frozenset(
            set(classification.observable_triggers) | {human_input_trigger.name}
        ),
        missing_fields=classification.missing_fields,
        computed_state=override.state,
        computed_mechanism=override.mechanism,
        outside_defined_playbooks=False,
        override_audit=audit,
    )
