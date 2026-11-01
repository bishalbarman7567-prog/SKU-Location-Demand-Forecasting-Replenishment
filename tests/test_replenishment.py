"""Unit Tests for Replenishment Policies, Constraints, and Exceptions."""

import unittest
from replenishment_engine.replenishment.policy import ReorderPolicyCalculator
from replenishment_engine.replenishment.recommender import ReplenishmentRecommender


class TestReplenishment(unittest.TestCase):
    """Test suite for safety stock calculations and constrained order sizing."""

    def test_reorder_policy_calculation(self):
        """Verifies combined variance safety stock formula."""
        res = ReorderPolicyCalculator.compute_policy_parameters(
            daily_demand_mean=10.0,
            daily_demand_std=2.0,
            nominal_lead_time_days=7.0,
            lead_time_std_days=1.5,
            review_period_days=1,
            service_level=0.95,
        )
        self.assertGreater(res["safety_stock_units"], 0)
        self.assertGreater(res["reorder_point_units"], res["safety_stock_units"])
        self.assertGreaterEqual(res["target_stock_level"], res["reorder_point_units"])

    def test_pack_size_and_moq_constraints(self):
        """Verifies that final_order_qty satisfies both pack size and MOQ."""
        rec = ReplenishmentRecommender.evaluate_replenishment(
            store_id="STORE-000001",
            sku_id="SKU-000001",
            supplier_id="SUPP-0001",
            recommendation_date="2025-03-31",
            current_on_hand_qty=5,
            current_on_order_qty=0,
            current_reserved_qty=0,
            reorder_point=50,
            target_stock_level=100,
            max_store_capacity_units=1000,
            pack_size=12,
            moq_units=48,
            unit_cost=5.00,
            sku_status="ACTIVE",
        )
        # Gross need: 100 - 5 = 95. MOQ is 48.
        # Pack size is 12: ceil(95 / 12) * 12 = 8 * 12 = 96.
        self.assertEqual(rec["final_order_qty"], 96)
        self.assertEqual(rec["final_order_qty"] % 12, 0)
        self.assertGreaterEqual(rec["final_order_qty"], 48)
        self.assertEqual(rec["exception_code"], "NONE")
        self.assertEqual(rec["status"], "RECOMMENDED")

    def test_discontinued_sku_exception(self):
        """Verifies that discontinued SKUs have order suppressed and flagged as exception."""
        rec = ReplenishmentRecommender.evaluate_replenishment(
            store_id="STORE-000001",
            sku_id="SKU-000002",
            supplier_id="SUPP-0001",
            recommendation_date="2025-03-31",
            current_on_hand_qty=0,
            current_on_order_qty=0,
            current_reserved_qty=0,
            reorder_point=50,
            target_stock_level=100,
            max_store_capacity_units=1000,
            pack_size=6,
            moq_units=12,
            unit_cost=3.00,
            sku_status="DISCONTINUED",
        )
        self.assertEqual(rec["final_order_qty"], 0)
        self.assertEqual(rec["exception_code"], "ERR_DISCONTINUED_SKU")
        self.assertEqual(rec["status"], "REJECTED")

    def test_store_capacity_clipping(self):
        """Verifies that orders exceeding backroom storage capacity are clipped to pack size."""
        rec = ReplenishmentRecommender.evaluate_replenishment(
            store_id="STORE-000001",
            sku_id="SKU-000003",
            supplier_id="SUPP-0001",
            recommendation_date="2025-03-31",
            current_on_hand_qty=10,
            current_on_order_qty=0,
            current_reserved_qty=0,
            reorder_point=100,
            target_stock_level=500,
            max_store_capacity_units=80,  # Tight capacity
            pack_size=12,
            moq_units=24,
            unit_cost=4.00,
            sku_status="ACTIVE",
        )
        # Remaining capacity: 80 - 10 = 70.
        # Max multiple of 12 <= 70 is 5 * 12 = 60.
        self.assertEqual(rec["final_order_qty"], 60)
        self.assertEqual(rec["exception_code"], "ERR_CAPACITY_EXCEEDED")
        self.assertEqual(rec["status"], "EXCEPTION_FLAGGED")


if __name__ == "__main__":
    unittest.main()

