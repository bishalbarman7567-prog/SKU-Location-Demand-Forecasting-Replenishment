"""Unit Tests for Referential Integrity, Enums, and Reproducibility."""

import unittest
from replenishment_engine.generator.synthetic_data_generator import ReplenishmentDataGenerator
from replenishment_engine.validation.data_validator import DataValidator
from replenishment_engine.validation.audit import verify_reproducibility
from replenishment_engine.config import DEFAULT_RANDOM_SEED


class TestValidation(unittest.TestCase):
    """Test suite for full relational validation and audit verification."""

    @classmethod
    def setUpClass(cls):
        cls.gen = ReplenishmentDataGenerator(seed=DEFAULT_RANDOM_SEED, profile_name="starter")
        cls.tables = cls.gen.generate_all()

    def test_baseline_dataset_validity(self):
        """Verifies clean baseline dataset passes 100% of validation rules."""
        report = DataValidator.validate_dataset_bundle(self.tables)
        self.assertTrue(report["is_valid"], f"Validation failed with: {report['failures']}")
        self.assertEqual(report["failed_checks"], 0)
        self.assertGreater(report["passed_checks"], 15)

    def test_foreign_key_referential_integrity(self):
        """Specifically verifies zero orphaned foreign key records."""
        report = DataValidator.validate_dataset_bundle(self.tables)
        fk_failures = [f for f in report["failures"] if "FK" in f["check"]]
        self.assertEqual(len(fk_failures), 0)

    def test_step_10_reproducibility(self):
        """Executes Step 10 acceptance check verifying identical hash and rows on regeneration."""
        audit_res = verify_reproducibility(seed=DEFAULT_RANDOM_SEED, profile="starter")
        self.assertTrue(audit_res["is_reproducible"])
        for tbl_name, details in audit_res["table_details"].items():
            self.assertTrue(
                details["bit_for_bit_identical"],
                f"Table {tbl_name} failed bit-for-bit reproducibility check",
            )


if __name__ == "__main__":
    unittest.main()

