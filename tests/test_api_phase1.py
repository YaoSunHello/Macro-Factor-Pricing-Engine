import json
import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from macro_factor_pricing_engine.api import app, serialize_recommendation, state_payload
from macro_factor_pricing_engine.app import run_analysis
from macro_factor_pricing_engine.regimes import (
    DEFINED_REGIME_PAIRS,
    CausalMechanism,
    MacroState,
    REGIME_DEFINITIONS,
    RegimeProbabilities,
)


class ApiPhase1Tests(unittest.TestCase):
    def test_state_payload_is_valid_json_and_distribution_sums_to_one(self):
        payload = state_payload()
        encoded = json.dumps(payload)

        self.assertTrue(encoded)
        self.assertAlmostEqual(
            sum(regime["weight"] for regime in payload["regime_distribution"]),
            1.0,
            delta=1e-9,
        )
        self.assertEqual(len(payload["macro_states"]), 6)
        self.assertEqual(len(payload["causal_mechanisms"]), 4)
        self.assertEqual(len(payload["defined_pairs"]), len(DEFINED_REGIME_PAIRS))
        self.assertEqual(len(payload["defined_pairs"]), 8)

    def test_transition_flag_uses_max_mass_threshold(self):
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            recommendation = run_analysis(
                inventory_path=tmp_path / "inventory.json",
                turnover_log_path=tmp_path / "turnover_ledger.jsonl",
            )

        low_mass = RegimeProbabilities(
            {
                REGIME_DEFINITIONS[0]: 0.55,
                REGIME_DEFINITIONS[1]: 0.45,
            }
        )
        payload = serialize_recommendation(
            replace(recommendation, regime_probabilities=low_mass)
        )

        self.assertTrue(payload["is_transition"])
        self.assertEqual(payload["max_mass"], 0.55)

    def test_defined_pairs_are_serialized_as_state_mechanism_values(self):
        payload = state_payload()
        defined_pairs = {
            (pair["state"], pair["mechanism"])
            for pair in payload["defined_pairs"]
        }

        self.assertIn(
            (
                MacroState.STAGFLATION.value,
                CausalMechanism.DELIBERATE_POLICY_DISRUPTION.value,
            ),
            defined_pairs,
        )

    def test_frontend_phase1_is_read_only(self):
        html = Path("frontend/index.html").read_text()

        self.assertIn("regime-grid", html)
        self.assertIn("transition-banner", html)
        self.assertNotIn("<input", html)
        self.assertNotIn("<textarea", html)
        self.assertNotIn("<select", html)

    @unittest.skipIf(app is None, "FastAPI dependency is not installed")
    def test_get_api_state_returns_json_when_fastapi_is_available(self):
        from fastapi.testclient import TestClient

        response = TestClient(app).get("/api/state")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("regime_distribution", payload)
        self.assertAlmostEqual(
            sum(regime["weight"] for regime in payload["regime_distribution"]),
            1.0,
            delta=1e-9,
        )


if __name__ == "__main__":
    unittest.main()
