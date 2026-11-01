"""Replenishment Recommendation Engine with Constraints & Exception Handling.

Evaluates net inventory positions against reorder policies, enforces supplier
pack sizes, minimum order quantities (MOQ), and facility capacity constraints,
and routes operational exceptions with transparent rationales.
"""

import math
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd


class ReplenishmentRecommender:
    """Generates constrained purchase recommendations and event lifecycle transitions."""

    @staticmethod
    def evaluate_replenishment(
        store_id: str,
        sku_id: str,
        supplier_id: str,
        recommendation_date: str,
        current_on_hand_qty: int,
        current_on_order_qty: int,
        current_reserved_qty: int,
        reorder_point: int,
        target_stock_level: int,
        max_store_capacity_units: int,
        pack_size: int,
        moq_units: int,
        unit_cost: float,
        sku_status: str = "ACTIVE",
        nominal_lead_time_days: int = 7,
    ) -> Dict[str, Any]:
        """Calculates purchase recommendation respecting all ordering constraints.

        Constraints:
        1. Net inventory position: IP = OnHand + OnOrder - Reserved
        2. Trigger rule: Order if IP <= ROP
        3. Gross Need: max(0, TSL - IP)
        4. Supplier MOQ constraint: max(GrossNeed, MOQ)
        5. Master pack size constraint: ceil(Need / PackSize) * PackSize
        6. Store capacity constraint: Cannot exceed max_store_capacity_units
        7. Merchandising exception: Discontinued products must not be replenished
        """
        inventory_position = current_on_hand_qty + current_on_order_qty - current_reserved_qty

        # 1. Check if replenishment trigger is reached
        needs_reorder = inventory_position <= reorder_point

        if not needs_reorder:
            return {
                "store_id": store_id,
                "sku_id": sku_id,
                "supplier_id": supplier_id,
                "recommendation_date": recommendation_date,
                "current_on_hand_qty": current_on_hand_qty,
                "current_on_order_qty": current_on_order_qty,
                "current_reserved_qty": current_reserved_qty,
                "net_inventory_position": inventory_position,
                "reorder_point": reorder_point,
                "target_stock_level": target_stock_level,
                "gross_need_units": 0,
                "unrounded_order_qty": 0,
                "pack_size_applied": pack_size,
                "moq_applied": moq_units,
                "capacity_constrained_qty": 0,
                "final_order_qty": 0,
                "unit_cost": unit_cost,
                "total_cost": 0.0,
                "priority": "ROUTINE",
                "status": "RECOMMENDED",
                "exception_code": "NONE",
                "rationale": f"Net inventory position ({inventory_position}) is healthy; strictly above ROP ({reorder_point}). No order needed.",
            }

        # 2. Check Discontinued SKU Exception
        if sku_status == "DISCONTINUED":
            return {
                "store_id": store_id,
                "sku_id": sku_id,
                "supplier_id": supplier_id,
                "recommendation_date": recommendation_date,
                "current_on_hand_qty": current_on_hand_qty,
                "current_on_order_qty": current_on_order_qty,
                "current_reserved_qty": current_reserved_qty,
                "net_inventory_position": inventory_position,
                "reorder_point": reorder_point,
                "target_stock_level": target_stock_level,
                "gross_need_units": max(0, target_stock_level - inventory_position),
                "unrounded_order_qty": 0,
                "pack_size_applied": pack_size,
                "moq_applied": moq_units,
                "capacity_constrained_qty": 0,
                "final_order_qty": 0,
                "unit_cost": unit_cost,
                "total_cost": 0.0,
                "priority": "HIGH_RISK",
                "status": "REJECTED",
                "exception_code": "ERR_DISCONTINUED_SKU",
                "rationale": f"EXCEPTION: SKU {sku_id} is DISCONTINUED in master catalog. Replenishment suppressed per merchandising governance rules.",
            }

        # 3. Check Negative Lead Time Exception
        if nominal_lead_time_days < 0:
            return {
                "store_id": store_id,
                "sku_id": sku_id,
                "supplier_id": supplier_id,
                "recommendation_date": recommendation_date,
                "current_on_hand_qty": current_on_hand_qty,
                "current_on_order_qty": current_on_order_qty,
                "current_reserved_qty": current_reserved_qty,
                "net_inventory_position": inventory_position,
                "reorder_point": reorder_point,
                "target_stock_level": target_stock_level,
                "gross_need_units": 0,
                "unrounded_order_qty": 0,
                "pack_size_applied": pack_size,
                "moq_applied": moq_units,
                "capacity_constrained_qty": 0,
                "final_order_qty": 0,
                "unit_cost": unit_cost,
                "total_cost": 0.0,
                "priority": "HIGH_RISK",
                "status": "EXCEPTION_FLAGGED",
                "exception_code": "ERR_NEGATIVE_LEAD_TIME",
                "rationale": f"CRITICAL: Invalid nominal lead time ({nominal_lead_time_days} days) for supplier {supplier_id}. Reorder halted.",
            }

        # 4. Standard Order Sizing Logic
        gross_need = max(0, target_stock_level - inventory_position)
        unrounded_qty = max(gross_need, moq_units) if gross_need > 0 else 0

        # Round up to master pack size multiple
        pack_rounded_qty = int(math.ceil(unrounded_qty / max(1, pack_size)) * pack_size)

        # 5. Store Backroom / Shelf Capacity Constraint
        remaining_capacity = max(0, max_store_capacity_units - inventory_position)
        if pack_rounded_qty > remaining_capacity:
            # Capacity exceeded: clip to capacity rounded down to pack size
            capped_qty = max(0, (remaining_capacity // pack_size) * pack_size)
            final_qty = capped_qty
            exception_code = "ERR_CAPACITY_EXCEEDED"
            status = "EXCEPTION_FLAGGED"
            rationale = (
                f"CAPACITY WARNING: Calculated order of {pack_rounded_qty} exceeds remaining store capacity "
                f"({remaining_capacity} units). Clipped to {final_qty} units (multiple of pack size {pack_size})."
            )
        else:
            final_qty = pack_rounded_qty
            exception_code = "NONE"
            status = "RECOMMENDED"
            rationale = (
                f"Position {inventory_position} <= ROP {reorder_point}. Ordering {final_qty} units "
                f"(GrossNeed={gross_need}, MOQ={moq_units}, PackSize={pack_size})."
            )

        # 6. Priority Classification
        if current_on_hand_qty == 0:
            priority = "CRITICAL_STOCKOUT"
        elif inventory_position < (reorder_point // 2):
            priority = "HIGH_RISK"
        else:
            priority = "ROUTINE"

        total_cost = round(final_qty * unit_cost, 2)

        return {
            "store_id": store_id,
            "sku_id": sku_id,
            "supplier_id": supplier_id,
            "recommendation_date": recommendation_date,
            "current_on_hand_qty": current_on_hand_qty,
            "current_on_order_qty": current_on_order_qty,
            "current_reserved_qty": current_reserved_qty,
            "net_inventory_position": inventory_position,
            "reorder_point": reorder_point,
            "target_stock_level": target_stock_level,
            "gross_need_units": gross_need,
            "unrounded_order_qty": unrounded_qty,
            "pack_size_applied": pack_size,
            "moq_applied": moq_units,
            "capacity_constrained_qty": pack_rounded_qty if final_qty == pack_rounded_qty else final_qty,
            "final_order_qty": final_qty,
            "unit_cost": unit_cost,
            "total_cost": total_cost,
            "priority": priority,
            "status": status,
            "exception_code": exception_code,
            "rationale": rationale,
        }

    @staticmethod
    def transition_lifecycle_state(
        recommendation: Dict[str, Any],
        target_status: str,
        actor: str,
        action: str,
        notes: str,
        event_counter: int,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Updates recommendation status and emits an immutable OrderLifecycleEvent."""
        from_status = recommendation["status"]
        updated_rec = dict(recommendation)
        updated_rec["status"] = target_status

        event = {
            "event_id": f"EVT-{event_counter:06d}",
            "recommendation_id": recommendation["recommendation_id"],
            "from_status": from_status,
            "to_status": target_status,
            "actor": actor,
            "action": action,
            "notes": notes,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        return updated_rec, event

