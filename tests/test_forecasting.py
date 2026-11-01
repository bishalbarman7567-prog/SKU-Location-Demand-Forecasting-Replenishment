"""Unit Tests for Demand Forecasting, Uncensoring, and Temporal Holdout Evaluation."""

import unittest
import numpy as np
import pandas as pd
from replenishment_engine.forecasting.uncensor import DemandUncensorer
from replenishment_engine.forecasting.engine import DemandForecaster
from replenishment_engine.forecasting.evaluator import ForecastEvaluator
from replenishment_engine.generator.synthetic_data_generator import ReplenishmentDataGenerator
from replenishment_engine.config import DEFAULT_RANDOM_SEED


class TestForecasting(unittest.TestCase):
    """Test suite for forecasting algorithms and stockout uncensoring."""

    def test_demand_uncensoring(self):
        """Verifies that stockout zero-sales are adjusted upwards."""
        # Simulated series with 1 stockout day
        data = {
            "date": [f"2025-01-{i:02d}" for i in range(1, 11)],
            "units_sold": [10, 12, 11, 0, 9, 13, 10, 11, 12, 10],
            "stockout_flag": [False, False, False, True, False, False, False, False, False, False],
            "promotion_flag": [False] * 10,
        }
        df = pd.DataFrame(data)
        uncensored_df = DemandUncensorer.uncensor_sales_series(df)

        self.assertIn("uncensored_demand", uncensored_df.columns)
        self.assertIn("was_demand_imputed", uncensored_df.columns)

        # The 4th day had units_sold=0, but stockout_flag=True; it should be imputed > 0
        stockout_imputed = uncensored_df.loc[3, "uncensored_demand"]
        self.assertGreater(stockout_imputed, 0.0)
        self.assertTrue(uncensored_df.loc[3, "was_demand_imputed"])

    def test_holt_winters_and_croston(self):
        """Tests that forecasting algorithms return valid non-negative forecasts."""
        # Test regular series
        regular_series = [10.0 + (i % 7) for i in range(28)]
        hw_mean, hw_std, hw_preds = DemandForecaster.forecast_holt_winters(regular_series, horizon=14)
        self.assertGreater(hw_mean, 0.0)
        self.assertGreater(hw_std, 0.0)
        self.assertEqual(len(hw_preds), 14)

        # Test intermittent series with many zeroes
        intermittent_series = [0.0, 0.0, 3.0, 0.0, 0.0, 0.0, 4.0, 0.0, 0.0, 2.0]
        cr_mean, cr_std, cr_preds = DemandForecaster.forecast_croston(intermittent_series, horizon=14)
        self.assertGreater(cr_mean, 0.0)
        self.assertEqual(len(cr_preds), 14)

    def test_temporal_holdout_evaluation(self):
        """Tests temporal holdout split and metric computation."""
        gen = ReplenishmentDataGenerator(seed=DEFAULT_RANDOM_SEED, profile_name="starter")
        tables = gen.generate_all()
        eval_results = ForecastEvaluator.evaluate_temporal_holdout(tables["SalesHistory"], holdout_days=14)

        self.assertIn("censored_model_metrics", eval_results)
        self.assertIn("uncensored_model_metrics", eval_results)
        self.assertIn("censoring_impact_analysis", eval_results)

        censored = eval_results["censored_model_metrics"]
        uncensored = eval_results["uncensored_model_metrics"]

        # Assert metrics are finite non-negative numbers
        self.assertGreaterEqual(censored["wape"], 0.0)
        self.assertGreaterEqual(uncensored["wape"], 0.0)
        self.assertGreaterEqual(censored["rmse"], 0.0)
        self.assertGreaterEqual(uncensored["rmse"], 0.0)


if __name__ == "__main__":
    unittest.main()

