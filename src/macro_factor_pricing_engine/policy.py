"""Strategy policy, trigger records, and governance rules."""

from dataclasses import dataclass


@dataclass(frozen=True)
class StrategyTrigger:
    """A condition that can cause review, rebalance, or risk reduction."""

    name: str
    trigger_type: str
    condition: str
    action: str
    requires_confirmation: bool


@dataclass(frozen=True)
class StrategyPolicy:
    """Strategy-level rules that sit above signal and allocation modules."""

    objective: str
    instrument_universe_status: str
    rebalance_rule: str
    no_trade_band: str
    risk_controls: tuple[str, ...]
    data_governance: tuple[str, ...]
    human_input_policy: tuple[str, ...]
    triggers: tuple[StrategyTrigger, ...]


def build_default_policy() -> StrategyPolicy:
    """Return the current policy record for the first implementation phase."""
    return StrategyPolicy(
        objective=(
            "Maximise risk-adjusted return using Sharpe and Calmar as primary "
            "targets, while every allocation must state macro reasoning."
        ),
        instrument_universe_status=(
            "Asset classes are approved, but ticker dictionaries are intentionally "
            "empty. No live or paper trade is allowed until instruments are approved."
        ),
        rebalance_rule=(
            "Evaluate signals after all required public data for the day is available. "
            "Rebalance on scheduled monthly review or when a material regime/risk "
            "trigger fires, subject to no-lookahead data availability."
        ),
        no_trade_band=(
            "Do not trade if proposed sleeve weight change is inside the future "
            "allocation module's no-trade threshold. Threshold value is not set yet."
        ),
        risk_controls=(
            "No lookahead: each data point must be lagged to its public availability date.",
            "No unapproved ticker can receive a target weight.",
            "Human input can only create a pending adjustment, never an automatic trade.",
            "Risk model, vol target, concentration caps, and turnover budget are pending Module 4.",
        ),
        data_governance=(
            "Record source, release cadence, release lag, and transformation for every indicator.",
            "Prefer vintage or release-date-aware data where available.",
            "Missing data handling must be explicit before a signal is computed.",
        ),
        human_input_policy=(
            "Normalize free text into structured macro claims.",
            "Tag each claim to growth, inflation, policy/liquidity, or risk appetite.",
            "Ask targeted validation questions when source quality or interpretation is unclear.",
            "Require explicit user confirmation before any validated claim can affect weights.",
        ),
        triggers=(
            StrategyTrigger(
                name="scheduled_monthly_review",
                trigger_type="calendar",
                condition="First trading day after month-end data is available.",
                action="Refresh regime state and compute proposed target weights.",
                requires_confirmation=False,
            ),
            StrategyTrigger(
                name="regime_transition",
                trigger_type="macro",
                condition="Confirmed regime score changes from one regime to another.",
                action="Open an allocation review and record the causal macro explanation.",
                requires_confirmation=False,
            ),
            StrategyTrigger(
                name="policy_shock",
                trigger_type="macro",
                condition="Front-end rates, real yields, or financial conditions tighten sharply.",
                action="Review beta and duration exposure; prefer cash/short duration until confirmed stable.",
                requires_confirmation=False,
            ),
            StrategyTrigger(
                name="liquidity_stress",
                trigger_type="risk",
                condition="Credit spreads widen quickly, USD rises, or drawdown/stress thresholds are breached.",
                action="Review defensive allocation and reduce drawdown-prone sleeves where policy allows.",
                requires_confirmation=False,
            ),
            StrategyTrigger(
                name="human_input_pending",
                trigger_type="governance",
                condition="User submits article, observation, or X post with market implications.",
                action="Create pending confidence-weighted signal adjustment and ask validation questions.",
                requires_confirmation=True,
            ),
            StrategyTrigger(
                name="instrument_universe_change",
                trigger_type="governance",
                condition="A ticker is proposed for an asset class.",
                action="Require approval before the ticker can be used in backtest, paper, or live allocation.",
                requires_confirmation=True,
            ),
        ),
    )
