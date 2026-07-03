import unittest
from dataclasses import replace
from datetime import date, datetime, timezone

from macro_factor_pricing_engine.data.regime_indicator_schema import (
    REGIME_INDICATOR_FIELDS,
    RegimeIndicatorSnapshot,
)
from macro_factor_pricing_engine.regime_classifier import (
    UNIMPLEMENTED_TRIGGER_STUBS,
    acm_term_premium_channel_contribution,
    classify_regime,
)
from macro_factor_pricing_engine.regime_override import RegimeOverride, apply_override
from macro_factor_pricing_engine.regimes import (
    CausalMechanism,
    MacroState,
    RegimeProbabilities,
    get_regime,
)


def median_snapshot(**overrides: float | None) -> RegimeIndicatorSnapshot:
    values = {
        "snapshot_date": date(2026, 7, 1),
        "ism_manufacturing_pmi": 51.0,
        "chicago_fed_nai": 0.0,
        "gdpnow_estimate": 2.0,
        "cpi_yoy": 2.7,
        "core_cpi_yoy": 2.8,
        "breakeven_5y5y": 2.3,
        "ust_2y_yield": 4.0,
        "ust_2y_yield_chg_1m": 0.0,
        "ust_10y_yield": 4.2,
        "ust_10y_yield_chg_1m": 0.0,
        "fed_funds_implied_path_chg_3m": 0.0,
        "nfci": 0.0,
        "ig_oas": 120.0,
        "ig_oas_chg_1m": 0.0,
        "hy_oas": 350.0,
        "hy_oas_chg_1m": 0.0,
        "vix": 18.0,
        "acm_term_premium_10y": 0.5,
        "dxy_chg_3m": 0.0,
        "dxy_trend_direction": 0.0,
        "broad_commodity_index_chg_3m": 0.0,
        "sp500_drawdown_from_52w_high": 5.0,
    }
    values.update(overrides)
    return RegimeIndicatorSnapshot(**values)


class RegimeClassifierSyntheticFixtureTests(unittest.TestCase):
    def test_goldilocks_fixture_classifies_to_cyclical_goldilocks(self):
        result = classify_regime(
            median_snapshot(
                ism_manufacturing_pmi=58.0,
                chicago_fed_nai=0.8,
                cpi_yoy=1.5,
                core_cpi_yoy=1.6,
                breakeven_5y5y=2.0,
                hy_oas=200.0,
                vix=12.0,
                nfci=-0.9,
            )
        )

        dominant = result.dominant_regime()
        self.assertEqual(dominant.state, MacroState.GOLDILOCKS)
        self.assertEqual(dominant.mechanism, CausalMechanism.CYCLICAL_NO_ACUTE_MECHANISM)
        ranked = sorted(result.weights.values(), reverse=True)
        self.assertGreaterEqual(ranked[0], ranked[1] * 2)

    def test_leverage_breakdown_fixture_combines_leverage_pairs(self):
        result = classify_regime(
            median_snapshot(
                ism_manufacturing_pmi=42.0,
                chicago_fed_nai=-1.2,
                cpi_yoy=None,
                core_cpi_yoy=None,
                breakeven_5y5y=None,
                hy_oas=850.0,
                hy_oas_chg_1m=250.0,
                vix=38.0,
                nfci=1.1,
            )
        )

        leverage_weight = sum(
            weight
            for regime, weight in result.weights.items()
            if regime.mechanism == CausalMechanism.LEVERAGE_INSTITUTIONAL_BREAKDOWN
        )
        non_leverage_weights = [
            sum(
                weight
                for regime, weight in result.weights.items()
                if regime.mechanism == mechanism
            )
            for mechanism in CausalMechanism
            if mechanism != CausalMechanism.LEVERAGE_INSTITUTIONAL_BREAKDOWN
        ]
        self.assertGreater(leverage_weight, max(non_leverage_weights))

    def test_missing_fields_degrade_gracefully_and_are_exposed(self):
        full = classify_regime(
            median_snapshot(
                ism_manufacturing_pmi=58.0,
                chicago_fed_nai=0.8,
                cpi_yoy=1.5,
                core_cpi_yoy=1.6,
                breakeven_5y5y=2.0,
                hy_oas=200.0,
                vix=12.0,
                nfci=-0.9,
            )
        )
        missing_field_names = tuple(REGIME_INDICATOR_FIELDS[:9])
        sparse_snapshot = median_snapshot(
            **{field_name: None for field_name in missing_field_names}
        )
        sparse = classify_regime(sparse_snapshot)

        self.assertEqual(sparse.missing_fields, frozenset(missing_field_names))
        self.assertLess(max(sparse.weights.values()), max(full.weights.values()))
        self.assertAlmostEqual(sum(sparse.weights.values()), 1.0, delta=1e-9)

    def test_unimplemented_threshold_stubs_raise_directly(self):
        snapshot = median_snapshot()
        for trigger_name, stub in UNIMPLEMENTED_TRIGGER_STUBS.items():
            with self.subTest(trigger_name=trigger_name):
                with self.assertRaises(NotImplementedError):
                    stub(snapshot)
        with self.assertRaises(NotImplementedError):
            acm_term_premium_channel_contribution(snapshot)

    def test_override_applies_full_weight_and_records_confirmation_policy(self):
        computed = classify_regime(median_snapshot())
        override = RegimeOverride(
            state=MacroState.REFLATION,
            mechanism=CausalMechanism.CYCLICAL_NO_ACUTE_MECHANISM,
            confidence=0.9,
            reason="Human-labeled fiscal impulse scenario.",
            entered_by="test",
            entered_at=datetime(2026, 7, 1, tzinfo=timezone.utc),
            expires_at=None,
        )

        result = apply_override(computed, override)

        self.assertEqual(
            result.dominant_regime(),
            get_regime(MacroState.REFLATION, CausalMechanism.CYCLICAL_NO_ACUTE_MECHANISM),
        )
        self.assertEqual(max(result.weights.values()), 1.0)
        self.assertEqual(result.override_audit.policy_trigger_name, "human_input_pending")
        self.assertTrue(result.override_audit.requires_confirmation)

    def test_override_undefined_pair_raises_key_error(self):
        computed = classify_regime(median_snapshot())
        override = RegimeOverride(
            state=MacroState.GOLDILOCKS,
            mechanism=CausalMechanism.PEG_OR_PROMISE_BREAK,
            confidence=0.9,
            reason="Undefined pair should fail.",
            entered_by="test",
            entered_at=datetime(2026, 7, 1, tzinfo=timezone.utc),
            expires_at=None,
        )

        with self.assertRaises(KeyError):
            apply_override(computed, override)

    def test_classification_round_trips_through_regime_probabilities_validation(self):
        result = classify_regime(median_snapshot())
        round_trip = RegimeProbabilities(result.weights)

        self.assertTrue(all(weight >= 0 for weight in round_trip.weights.values()))
        self.assertAlmostEqual(sum(round_trip.weights.values()), 1.0, delta=1e-9)

    def test_undefined_pair_fallback_uses_same_state_defined_pairs(self):
        result = classify_regime(
            median_snapshot(
                ism_manufacturing_pmi=44.0,
                chicago_fed_nai=-0.8,
                gdpnow_estimate=-0.2,
                cpi_yoy=5.0,
                core_cpi_yoy=4.8,
                breakeven_5y5y=3.6,
                hy_oas=300.0,
                hy_oas_chg_1m=0.0,
                vix=20.0,
                nfci=0.0,
                sp500_drawdown_from_52w_high=8.0,
            )
        )

        self.assertTrue(result.outside_defined_playbooks)
        self.assertEqual(result.computed_state, MacroState.STAGFLATION)
        self.assertEqual(result.computed_mechanism, CausalMechanism.CYCLICAL_NO_ACUTE_MECHANISM)
        self.assertEqual(
            {regime.state for regime in result.weights},
            {MacroState.STAGFLATION},
        )
        self.assertEqual(len(result.weights), 2)
        self.assertAlmostEqual(sum(result.weights.values()), 1.0, delta=1e-9)


class RegimeClassifierRealSnapshotSmokeTests(unittest.TestCase):
    def test_real_dated_snapshot_smoke_test_does_not_assert_label(self):
        snapshot = replace(
            median_snapshot(),
            snapshot_date=date(2026, 7, 1),
            ism_manufacturing_pmi=49.5,
            chicago_fed_nai=-0.1,
            gdpnow_estimate=1.6,
            cpi_yoy=4.2,
            core_cpi_yoy=3.6,
            breakeven_5y5y=2.4,
            ust_2y_yield=4.19,
            ust_10y_yield=4.46,
            nfci=-0.05,
            hy_oas=390.0,
            vix=18.0,
            acm_term_premium_10y=0.73,
            dxy_chg_3m=2.8,
            dxy_trend_direction=1.0,
        )

        result = classify_regime(snapshot)

        self.assertTrue(all(weight >= 0 for weight in result.weights.values()))
        self.assertAlmostEqual(sum(result.weights.values()), 1.0, delta=1e-9)
        self.assertFalse(result.missing_fields)
        print(
            "real_snapshot_smoke",
            result.dominant_regime().name,
            result.is_transition(),
        )


if __name__ == "__main__":
    unittest.main()
