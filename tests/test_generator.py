"""Unit Tests for Synthetic Data Generator and Anomaly Injection."""

import unittest
import pandas as pd
from replenishment_engine.generator.synthetic_data_generator import ReplenishmentDataGenerator
from replenishment_engine.generator.anomaly_injector import AnomalyInjector
from replenishment_engine.config import DEFAULT_RANDOM_SEED


class TestGenerator(unittest.TestCase):
    """Test suite for deterministic generation and structural invariants."""

    @classmethod
    def setUpClass(cls):
        cls.gen = ReplenishmentDataGenerator(seed=DEFAULT_RANDOM_SEED, profile_name="starter")
        cls.tables = cls.gen.generate_all()

    def test_all_entities_present(self):
        """Verifies all 10 core entities plus audit events are generated."""
        expected_entities = [
            "SKU", "Store", "Supplier", "SupplierSKU",
            "SalesHistory", "InventorySnapshot", "LeadTimeObservation",
            "Forecast", "ReorderPolicy", "PurchaseRecommendation", "OrderLifecycleEvent"
        ]
        for ent in expected_entities:
            self.assertIn(ent, self.tables)
            self.assertGreater(len(self.tables[ent]), 0, f"Table {ent} should not be empty")

    def test_id_nomenclature_conventions(self):
        """Checks zero-padded deterministic ID patterns."""
        skus = self.tables["SKU"]
        stores = self.tables["Store"]
        sales = self.tables["SalesHistory"]
        recs = self.tables["PurchaseRecommendation"]

        # Check SKU ID format: SKU-000001
        self.assertTrue(skus["sku_id"].str.match(r"^SKU-\d{6}$").all())
        # Check Store ID format: STORE-000001
        self.assertTrue(stores["store_id"].str.match(r"^STORE-\d{6}$").all())
        # Check Sale ID format: SALE-STORE-XXXXXX-SKU-XXXXXX-YYYY-MM-DD
        self.assertTrue(sales["sale_id"].str.match(r"^SALE-STORE-\d{6}-SKU-\d{6}-\d{4}-\d{2}-\d{2}$").all())
        # Check Recommendation ID format: PO-YYYY-XXXXXX
        self.assertTrue(recs["recommendation_id"].str.match(r"^PO-\d{4}-\d{6}$").all())

    def test_anomaly_injection_and_ground_truth_segregation(self):
        """Checks that all 5 edge cases are injected and tracked in ground_truth without feature leakage."""
        injector = AnomalyInjector(seed=DEFAULT_RANDOM_SEED)
        sales_mod, lead_mod, recs_mod, fc_mod, gt = injector.inject_all_anomalies(
            self.tables["SalesHistory"],
            self.tables["LeadTimeObservation"],
            self.tables["PurchaseRecommendation"],
            self.tables["Forecast"],
            self.tables["SKU"],
        )

        gt_df = pd.DataFrame(gt)
        self.assertGreater(len(gt_df), 0)

        # Check all 5 required issue types are represented
        issue_types = set(gt_df["issue_type"].unique())
        expected_issues = {
            "STOCKOUT_CENSORED_AS_ZERO",
            "PACK_SIZE_VIOLATION",
            "DISCONTINUED_SKU_ORDERED",
            "NEGATIVE_LEAD_TIME",
            "DATA_LEAKAGE_FUTURE_SALES",
        }
        self.assertEqual(expected_issues, issue_types)

        # Verify ground truth fields are NOT columns in the core operational tables
        self.assertNotIn("issue_type", sales_mod.columns)
        self.assertNotIn("issue_type", recs_mod.columns)
        self.assertNotIn("anomaly_id", lead_mod.columns)


if __name__ == "__main__":
    unittest.main()

