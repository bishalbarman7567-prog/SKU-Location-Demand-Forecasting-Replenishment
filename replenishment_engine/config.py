"""Configuration and Scale Profiles for SKU-Location Replenishment Engine.

Provides deterministic random seeds, scale profiles (starter, medium, full),
and constants for entities and business rules.
"""

from dataclasses import dataclass
from typing import Dict, Any


DEFAULT_RANDOM_SEED = 20261022


@dataclass(frozen=True)
class ScaleProfile:
    """Scale configuration for data generation."""
    name: str
    num_skus: int
    num_stores: int
    num_suppliers: int
    num_days: int
    start_date: str = "2025-01-01"


# Scale profiles: starter (quick execution/testing), medium, and full baseline
SCALE_PROFILES: Dict[str, ScaleProfile] = {
    "starter": ScaleProfile(
        name="starter",
        num_skus=50,
        num_stores=5,
        num_suppliers=10,
        num_days=90,
        start_date="2025-01-01",
    ),
    "medium": ScaleProfile(
        name="medium",
        num_skus=200,
        num_stores=20,
        num_suppliers=25,
        num_days=180,
        start_date="2025-01-01",
    ),
    "full": ScaleProfile(
        name="full",
        num_skus=2000,
        num_stores=100,
        num_suppliers=50,
        num_days=365,
        start_date="2025-01-01",
    ),
}

# Domain taxonomies
SKU_CATEGORIES = [
    "Beverages",
    "Dairy",
    "Bakery",
    "Pantry",
    "Produce",
    "Frozen",
    "Personal Care",
    "Household",
]

STORE_CHANNELS = [
    "RETAIL_SUPERMARKET",
    "CONVENIENCE",
    "ECOMM_HUB",
    "REGIONAL_DC",
]

STORE_REGIONS = [
    "North",
    "South",
    "East",
    "West",
    "Central",
]

SUPPLIER_TIERS = [
    "TIER_1",
    "TIER_2",
    "TIER_3",
]

SKU_STATUSES = [
    "ACTIVE",
    "PHASE_OUT",
    "DISCONTINUED",
]

REORDER_PRIORITIES = [
    "CRITICAL_STOCKOUT",
    "HIGH_RISK",
    "ROUTINE",
    "SEASONAL_BUILD",
]

RECOMMENDATION_STATUSES = [
    "RECOMMENDED",
    "APPROVED",
    "REJECTED",
    "EXCEPTION_FLAGGED",
    "ORDERED",
]

EXCEPTION_CODES = [
    "NONE",
    "ERR_DISCONTINUED_SKU",
    "ERR_CAPACITY_EXCEEDED",
    "ERR_PACK_SIZE_MISMATCH",
    "ERR_NEGATIVE_LEAD_TIME",
    "ERR_SUPPLIER_INACTIVE",
]

