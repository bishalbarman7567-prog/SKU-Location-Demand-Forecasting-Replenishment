"""Reorder Policy & Parameter Calculation Engine.

Calculates mathematically rigorous Safety Stock, Reorder Point (ROP),
and Target Stock Level (TSL) incorporating both demand variance and lead-time variance.
"""

import math
from typing import Dict, Any, Optional
import numpy as np


class ReorderPolicyCalculator:
    """Computes inventory parameters for SKU-Store replenishment."""

    Z_TABLE = {
        0.80: 0.842,
        0.85: 1.036,
        0.90: 1.282,
        0.95: 1.645,
        0.98: 2.054,
        0.99: 2.326,
        0.999: 3.090,
    }

    @classmethod
    def get_z_factor(cls, service_level: float) -> float:
        """Looks up or interpolates standard normal score for desired cycle service level."""
        closest_key = min(cls.Z_TABLE.keys(), key=lambda k: abs(k - service_level))
        return cls.Z_TABLE[closest_key]

    @classmethod
    def compute_policy_parameters(
        cls,
        daily_demand_mean: float,
        daily_demand_std: float,
        nominal_lead_time_days: float,
        lead_time_std_days: float,
        review_period_days: int = 1,
        service_level: float = 0.95,
        store_max_capacity_units: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Calculates safety stock, ROP, and target stock level.

        Formula:
        SS = Z * sqrt(L * sigma_d^2 + d^2 * sigma_L^2)
        ROP = (d * L) + SS
        TSL = ROP + (ReviewPeriod * d)
        """
        d = max(0.01, float(daily_demand_mean))
        sigma_d = max(0.05, float(daily_demand_std))
        L = max(1.0, float(nominal_lead_time_days))
        sigma_L = max(0.0, float(lead_time_std_days))
        z = cls.get_z_factor(service_level)

        # Combined variance accounting for demand volatility AND supplier lead time volatility
        combined_variance = (L * (sigma_d ** 2)) + ((d ** 2) * (sigma_L ** 2))
        safety_stock = int(math.ceil(z * math.sqrt(combined_variance)))

        lead_time_demand = round(d * L, 2)
        reorder_point = int(math.ceil(lead_time_demand + safety_stock))
        target_stock_level = int(math.ceil(reorder_point + (review_period_days * d)))

        if store_max_capacity_units is None:
            store_max_capacity_units = target_stock_level * 3

        return {
            "service_level": service_level,
            "z_factor": z,
            "effective_lead_time_days": L,
            "lead_time_demand": lead_time_demand,
            "safety_stock_units": safety_stock,
            "reorder_point_units": reorder_point,
            "target_stock_level": target_stock_level,
            "review_period_days": review_period_days,
            "max_store_capacity_units": store_max_capacity_units,
        }

