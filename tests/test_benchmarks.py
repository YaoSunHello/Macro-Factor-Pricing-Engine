import unittest

from macro_factor_pricing_engine.benchmarks import (
    HORIZON_BENCHMARKS,
    HORIZONS,
    benchmark_weight,
)
from macro_factor_pricing_engine.universe import asset_classes


class BenchmarkTests(unittest.TestCase):
    def test_all_horizons_are_present(self):
        self.assertEqual(tuple(HORIZON_BENCHMARKS), HORIZONS)
        self.assertEqual(HORIZONS, ("10y", "5y", "1y", "1q"))

    def test_each_horizon_sums_to_one(self):
        for horizon, weights in HORIZON_BENCHMARKS.items():
            with self.subTest(horizon=horizon):
                self.assertAlmostEqual(sum(weights.values()), 1.0, delta=1e-9)

    def test_every_weight_key_is_an_asset_class(self):
        valid_asset_classes = set(asset_classes())
        for horizon, weights in HORIZON_BENCHMARKS.items():
            with self.subTest(horizon=horizon):
                self.assertTrue(set(weights).issubset(valid_asset_classes))

    def test_benchmark_weight_returns_zero_for_omitted_bucket(self):
        self.assertIn("usd_proxy", asset_classes())
        self.assertNotIn("usd_proxy", HORIZON_BENCHMARKS["10y"])
        self.assertEqual(benchmark_weight("10y", "usd_proxy"), 0.0)

    def test_one_quarter_is_cash_only(self):
        self.assertEqual(HORIZON_BENCHMARKS["1q"], {"cash": 1.0})


if __name__ == "__main__":
    unittest.main()
