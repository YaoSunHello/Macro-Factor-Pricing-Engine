import unittest

from macro_factor_pricing_engine.policy import build_default_policy
from macro_factor_pricing_engine.regimes import REGIME_DEFINITIONS
from macro_factor_pricing_engine.universe import ASSET_CLASS_UNIVERSE, has_tradeable_instruments


class UniverseTests(unittest.TestCase):
    def test_asset_classes_have_no_approved_tickers_yet(self):
        self.assertTrue(ASSET_CLASS_UNIVERSE)
        self.assertFalse(has_tradeable_instruments())
        self.assertTrue(all(instruments == {} for instruments in ASSET_CLASS_UNIVERSE.values()))


class RegimeTests(unittest.TestCase):
    def test_regimes_have_observable_triggers(self):
        self.assertGreaterEqual(len(REGIME_DEFINITIONS), 5)
        for regime in REGIME_DEFINITIONS:
            self.assertTrue(regime.observable_triggers)
            self.assertTrue(regime.causal_story)


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

    def test_policy_blocks_trading_without_tickers(self):
        policy = build_default_policy()
        self.assertIn("No live or paper trade is allowed", policy.instrument_universe_status)


if __name__ == "__main__":
    unittest.main()
