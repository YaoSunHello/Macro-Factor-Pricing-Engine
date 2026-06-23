import unittest

from macro_factor_pricing_engine.policy import build_default_policy
from macro_factor_pricing_engine.regimes import (
    DEFINED_REGIME_PAIRS,
    MACRO_TRANSMISSION_CHANNELS,
    REGIME_DEFINITIONS,
    UNDEFINED_REGIME_PAIR_RATIONALE,
    VALUATION_OVERLAY,
    CausalMechanism,
    MacroState,
    RegimeProbabilities,
    get_regime,
)
from macro_factor_pricing_engine.treasury_policy import build_treasury_policy
from macro_factor_pricing_engine.universe import (
    ASSET_CLASS_SCORING_MODULES,
    ASSET_CLASS_UNIVERSE,
    has_tradeable_instruments,
)


class UniverseTests(unittest.TestCase):
    def test_asset_classes_have_no_approved_tickers_yet(self):
        self.assertTrue(ASSET_CLASS_UNIVERSE)
        self.assertFalse(has_tradeable_instruments())
        self.assertTrue(all(instruments == {} for instruments in ASSET_CLASS_UNIVERSE.values()))

    def test_scoring_module_seam_is_unwired(self):
        self.assertEqual(set(ASSET_CLASS_UNIVERSE), set(ASSET_CLASS_SCORING_MODULES))
        self.assertTrue(all(module is None for module in ASSET_CLASS_SCORING_MODULES.values()))


class RegimeTests(unittest.TestCase):
    def test_regimes_have_observable_triggers_and_heuristic_priors(self):
        self.assertGreaterEqual(len(REGIME_DEFINITIONS), 5)
        for regime in REGIME_DEFINITIONS:
            self.assertIn((regime.state, regime.mechanism), DEFINED_REGIME_PAIRS)
            self.assertTrue(regime.observable_trigger_names)
            self.assertTrue(regime.causal_story)
            self.assertTrue(regime.asset_priors_are_heuristic)

    def test_only_meaningful_pairs_are_defined(self):
        expected_pairs = {
            (MacroState.GOLDILOCKS, CausalMechanism.CYCLICAL_NO_ACUTE_MECHANISM),
            (MacroState.REFLATION, CausalMechanism.CYCLICAL_NO_ACUTE_MECHANISM),
            (MacroState.STAGFLATION, CausalMechanism.DELIBERATE_POLICY_DISRUPTION),
            (MacroState.STAGFLATION, CausalMechanism.LEVERAGE_INSTITUTIONAL_BREAKDOWN),
            (MacroState.DISINFLATIONARY_SLOWDOWN, CausalMechanism.CYCLICAL_NO_ACUTE_MECHANISM),
            (MacroState.CRISIS_LIQUIDITY_STRESS, CausalMechanism.PEG_OR_PROMISE_BREAK),
            (MacroState.CRISIS_LIQUIDITY_STRESS, CausalMechanism.LEVERAGE_INSTITUTIONAL_BREAKDOWN),
            (MacroState.POLICY_TIGHTENING_SHOCK, CausalMechanism.DELIBERATE_POLICY_DISRUPTION),
        }
        self.assertEqual(DEFINED_REGIME_PAIRS, expected_pairs)
        self.assertTrue(UNDEFINED_REGIME_PAIR_RATIONALE)

    def test_stagflation_mechanism_flips_long_duration_positioning(self):
        policy_disruption = get_regime(
            MacroState.STAGFLATION,
            CausalMechanism.DELIBERATE_POLICY_DISRUPTION,
        )
        leverage_breakdown = get_regime(
            MacroState.STAGFLATION,
            CausalMechanism.LEVERAGE_INSTITUTIONAL_BREAKDOWN,
        )
        self.assertEqual(
            policy_disruption.asset_position("long_duration_government_bonds"),
            "strong_underweight",
        )
        self.assertEqual(
            leverage_breakdown.asset_position("long_duration_government_bonds"),
            "overweight",
        )

    def test_regime_probabilities_validate_sum_and_transition_threshold(self):
        first, second = REGIME_DEFINITIONS[:2]
        with self.assertRaises(ValueError):
            RegimeProbabilities({first: 0.7, second: 0.2})

        transition = RegimeProbabilities({first: 0.55, second: 0.45})
        self.assertTrue(transition.is_transition())

        dominant = RegimeProbabilities({first: 0.65, second: 0.35})
        self.assertFalse(dominant.is_transition())

    def test_valuation_overlay_is_not_macro_channel(self):
        self.assertIn("fiscal_sovereign", MACRO_TRANSMISSION_CHANNELS)
        self.assertNotIn("valuation_overlay", MACRO_TRANSMISSION_CHANNELS)
        self.assertFalse(VALUATION_OVERLAY.scoring_implemented)


class PolicyTests(unittest.TestCase):
    def test_human_input_and_universe_changes_require_confirmation(self):
        policy = build_default_policy()
        confirmation_triggers = {
            trigger.name
            for trigger in policy.triggers
            if trigger.requires_confirmation
        }
        self.assertIn("human_input_pending", confirmation_triggers)
        self.assertIn("instrument_universe_change", confirmation_triggers)

    def test_policy_blocks_trading_without_tickers_and_has_lag_budget(self):
        policy = build_default_policy()
        self.assertIn("No live or paper trade is allowed", policy.instrument_universe_status)
        self.assertTrue(policy.regime_detection_lag_budget)
        self.assertIn("Pending/unconfirmed", policy.benchmark_or_liability_reference)

    def test_regime_transition_trigger_uses_probability_mass(self):
        policy = build_default_policy()
        transition = next(trigger for trigger in policy.triggers if trigger.name == "regime_transition")
        self.assertIn("RegimeProbabilities", transition.condition)
        self.assertIn("probability-mass", transition.action)


class TreasuryPolicyTests(unittest.TestCase):
    def test_treasury_policy_is_structured_but_not_a_scorer(self):
        policy = build_treasury_policy()
        self.assertEqual(policy.version, "0.2")
        self.assertIn("fiscal_credibility_gate", policy.conceptual_blocks)
        self.assertTrue(policy.inputs)
        self.assertTrue(policy.signal_rules)
        self.assertTrue(policy.checklists)
        self.assertIn("Use as structured prior, not autopilot.", policy.governance)


if __name__ == "__main__":
    unittest.main()
