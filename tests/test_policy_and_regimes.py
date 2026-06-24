import unittest
from tempfile import TemporaryDirectory
from pathlib import Path

from macro_factor_pricing_engine.api_keys import (
    BROKER_API_SETUPS,
    Broker,
    all_broker_api_statuses,
    broker_api_status,
    get_broker_api_setup,
    load_broker_api_credentials,
    normalize_broker,
)
from macro_factor_pricing_engine.app import run_analysis
from macro_factor_pricing_engine.policy import build_default_policy
from macro_factor_pricing_engine.regimes import (
    DEFINED_REGIME_PAIRS,
    MACRO_TRANSMISSION_CHANNELS,
    MACRO_STATE_PROFILES,
    REGIME_DEFINITIONS,
    TRANSITION_MATRIX,
    UNDEFINED_REGIME_PAIR_RATIONALE,
    VALUATION_OVERLAY,
    CausalMechanism,
    MacroState,
    RegimeProbabilities,
    get_regime,
    transition_row_for,
)
from macro_factor_pricing_engine.treasury_policy import build_treasury_policy
from macro_factor_pricing_engine.universe import (
    ASSET_CLASS_SCORING_MODULES,
    ASSET_CLASS_UNIVERSE,
    has_tradeable_instruments,
    rates_securities,
)


class UniverseTests(unittest.TestCase):
    def test_asset_classes_have_membership_but_no_approved_tickers_yet(self):
        self.assertTrue(ASSET_CLASS_UNIVERSE)
        self.assertFalse(has_tradeable_instruments())
        self.assertTrue(rates_securities())
        self.assertTrue(
            all(not security["approved_for_allocation"] for security in rates_securities())
        )

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
            (MacroState.DISINFLATIONARY_SLOWDOWN, CausalMechanism.PEG_OR_PROMISE_BREAK),
            (MacroState.DISINFLATIONARY_SLOWDOWN, CausalMechanism.LEVERAGE_INSTITUTIONAL_BREAKDOWN),
            (MacroState.DISINFLATIONARY_SLOWDOWN, CausalMechanism.DELIBERATE_POLICY_DISRUPTION),
        }
        self.assertEqual(DEFINED_REGIME_PAIRS, expected_pairs)
        self.assertTrue(UNDEFINED_REGIME_PAIR_RATIONALE)

    def test_macro_state_taxonomy_has_four_structural_quadrants(self):
        self.assertEqual(len(MacroState), 4)
        self.assertEqual(set(MACRO_STATE_PROFILES), set(MacroState))

    def test_transition_matrix_rows_sum_to_one(self):
        self.assertEqual(set(TRANSITION_MATRIX), set(MacroState))
        for state, row in TRANSITION_MATRIX.items():
            with self.subTest(state=state):
                self.assertEqual(set(row), set(MacroState))
                self.assertTrue(all(probability >= 0 for probability in row.values()))
                self.assertAlmostEqual(sum(row.values()), 1.0, delta=1e-9)

    def test_leverage_breakdown_modifier_raises_slowdown_probability(self):
        base = TRANSITION_MATRIX[MacroState.GOLDILOCKS]
        modified = transition_row_for(
            MacroState.GOLDILOCKS,
            CausalMechanism.LEVERAGE_INSTITUTIONAL_BREAKDOWN,
        )

        self.assertGreater(
            modified[MacroState.DISINFLATIONARY_SLOWDOWN],
            base[MacroState.DISINFLATIONARY_SLOWDOWN],
        )
        self.assertAlmostEqual(sum(modified.values()), 1.0, delta=1e-9)

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


class BrokerApiSetupTests(unittest.TestCase):
    def test_requested_brokers_have_api_setups(self):
        self.assertEqual(
            set(BROKER_API_SETUPS),
            {
                Broker.TRADING212,
                Broker.INTERACTIVE_BROKERS,
                Broker.ROBINHOOD,
                Broker.IG_GROUP,
                Broker.CAPITAL_COM,
                Broker.PLUS500,
            },
        )
        self.assertEqual(normalize_broker("interactivebroker"), Broker.INTERACTIVE_BROKERS)
        self.assertEqual(normalize_broker("robinghood"), Broker.ROBINHOOD)
        self.assertEqual(get_broker_api_setup("capital.com").display_name, "Capital.com")

    def test_status_reports_missing_required_environment_without_secret_values(self):
        status = broker_api_status("ig group", environ={"IG_API_KEY": "secret"})

        self.assertFalse(status.configured)
        self.assertEqual(status.missing_required_env_vars, ("IG_USERNAME", "IG_PASSWORD"))
        self.assertNotIn("secret", repr(status))

    def test_credentials_load_from_environment_when_complete(self):
        credentials = load_broker_api_credentials(
            "capital.com",
            environ={
                "CAPITAL_COM_API_KEY": "key",
                "CAPITAL_COM_IDENTIFIER": "user@example.com",
                "CAPITAL_COM_API_PASSWORD": "password",
                "CAPITAL_COM_BASE_URL": "https://demo-api-capital.backend-capital.com/",
            },
        )

        self.assertEqual(credentials.setup.broker, Broker.CAPITAL_COM)
        self.assertEqual(credentials.values["CAPITAL_COM_API_KEY"], "key")
        self.assertEqual(
            credentials.values["CAPITAL_COM_BASE_URL"],
            "https://demo-api-capital.backend-capital.com/",
        )

    def test_unsupported_public_api_does_not_load_credentials(self):
        status = broker_api_status("plus500", environ={})

        self.assertFalse(status.configured)
        self.assertFalse(status.setup.execution_supported)
        with self.assertRaises(RuntimeError):
            load_broker_api_credentials("plus500", environ={})

    def test_all_statuses_cover_every_setup(self):
        statuses = all_broker_api_statuses(environ={})

        self.assertEqual(len(statuses), len(BROKER_API_SETUPS))
        self.assertEqual({status.setup.broker for status in statuses}, set(BROKER_API_SETUPS))


class TreasuryPolicyTests(unittest.TestCase):
    def test_treasury_policy_is_structured_but_not_a_scorer(self):
        policy = build_treasury_policy()
        self.assertEqual(policy.version, "0.2")
        self.assertIn("fiscal_credibility_gate", policy.conceptual_blocks)
        self.assertTrue(policy.inputs)
        self.assertTrue(policy.signal_rules)
        self.assertTrue(policy.checklists)
        self.assertIn("Use as structured prior, not autopilot.", policy.governance)


class RatesLoopTests(unittest.TestCase):
    def test_loop_runs_end_to_end_and_emits_pending_recommendation(self):
        with TemporaryDirectory() as tmp:
            recommendation = run_analysis(
                inventory_path=Path(tmp) / "inventory.json",
                turnover_log_path=Path(tmp) / "turnover.jsonl",
            )

            self.assertEqual(recommendation.mode, "analysis")
            self.assertEqual(recommendation.status, "PENDING")
            self.assertFalse(has_tradeable_instruments())
            self.assertAlmostEqual(recommendation.target.total_weight(), 1.0)
            self.assertGreater(recommendation.turnover_rows_appended, 0)
            self.assertIn("PENDING analysis recommendation only", recommendation.explanation)

    def test_turnover_log_appends(self):
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "turnover.jsonl"
            run_analysis(
                inventory_path=Path(tmp) / "inventory.json",
                turnover_log_path=ledger,
            )
            first_count = len(ledger.read_text().splitlines())

            run_analysis(
                inventory_path=Path(tmp) / "inventory.json",
                turnover_log_path=ledger,
            )
            second_count = len(ledger.read_text().splitlines())

            self.assertGreater(first_count, 0)
            self.assertEqual(second_count, first_count * 2)

    def test_snapshot_default_regime_reproduces_hand_calc_stance(self):
        """Wiring smoke only: proves loop reproduces one known hand calc, not policy validity."""
        with TemporaryDirectory() as tmp:
            recommendation = run_analysis(
                inventory_path=Path(tmp) / "inventory.json",
                turnover_log_path=Path(tmp) / "turnover.jsonl",
            )
            buckets = recommendation.target.bucket_weights()

            self.assertGreaterEqual(
                buckets["short_duration_government_bonds"]
                + buckets["intermediate_duration_government_bonds"],
                0.60,
            )
            self.assertLessEqual(buckets["long_duration_government_bonds"], 0.10)
            self.assertGreaterEqual(buckets["inflation_linked_bonds"], 0.25)


if __name__ == "__main__":
    unittest.main()
