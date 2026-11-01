"""Deterministic Master & Transaction Data Generator.

Generates 10 core entities in strict topological dependency order:
1. Master: SKU, Store, Supplier
2. Contracts / Matrix: SupplierSKU
3. Transactions / Events: SalesHistory, InventorySnapshot, LeadTimeObservation
4. Analytics & Decisions: Forecast, ReorderPolicy, PurchaseRecommendation
5. Audit Logs: OrderLifecycleEvent
"""

import math
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import numpy as np
import pandas as pd

from replenishment_engine.config import (
    DEFAULT_RANDOM_SEED,
    SCALE_PROFILES,
    ScaleProfile,
    SKU_CATEGORIES,
    STORE_CHANNELS,
    STORE_REGIONS,
    SUPPLIER_TIERS,
    SKU_STATUSES,
)


class ReplenishmentDataGenerator:
    """Generates synthetic, deterministic, relational supply chain data."""

    def __init__(self, seed: int = DEFAULT_RANDOM_SEED, profile_name: str = "starter"):
        self.seed = seed
        self.profile = SCALE_PROFILES.get(profile_name, SCALE_PROFILES["starter"])
        self.rng = np.random.RandomState(seed)
        self.start_date = datetime.strptime(self.profile.start_date, "%Y-%m-%d")

        # Container state
        self.skus: List[Dict[str, Any]] = []
        self.stores: List[Dict[str, Any]] = []
        self.suppliers: List[Dict[str, Any]] = []
        self.supplier_skus: List[Dict[str, Any]] = []
        self.sales_history: List[Dict[str, Any]] = []
        self.inventory_snapshots: List[Dict[str, Any]] = []
        self.lead_time_observations: List[Dict[str, Any]] = []
        self.forecasts: List[Dict[str, Any]] = []
        self.reorder_policies: List[Dict[str, Any]] = []
        self.purchase_recommendations: List[Dict[str, Any]] = []
        self.order_lifecycle_events: List[Dict[str, Any]] = []

    def generate_all(self) -> Dict[str, pd.DataFrame]:
        """Executes full end-to-end data generation pipeline in topological order."""
        self.generate_master_data()
        self.generate_supplier_sku_matrix()
        self.generate_sales_and_inventory_events()
        self.generate_forecasts_and_policies()
        self.generate_replenishment_decisions()
        self.generate_lifecycle_audit_events()

        return {
            "SKU": pd.DataFrame(self.skus),
            "Store": pd.DataFrame(self.stores),
            "Supplier": pd.DataFrame(self.suppliers),
            "SupplierSKU": pd.DataFrame(self.supplier_skus),
            "SalesHistory": pd.DataFrame(self.sales_history),
            "InventorySnapshot": pd.DataFrame(self.inventory_snapshots),
            "LeadTimeObservation": pd.DataFrame(self.lead_time_observations),
            "Forecast": pd.DataFrame(self.forecasts),
            "ReorderPolicy": pd.DataFrame(self.reorder_policies),
            "PurchaseRecommendation": pd.DataFrame(self.purchase_recommendations),
            "OrderLifecycleEvent": pd.DataFrame(self.order_lifecycle_events),
        }

    def generate_master_data(self):
        """Step 1 & 2: Generate parent master tables: SKU, Store, Supplier."""
        # 1. SKUs
        for i in range(1, self.profile.num_skus + 1):
            sku_id = f"SKU-{i:06d}"
            category = self.rng.choice(SKU_CATEGORIES)
            
            # Unit economics based on category
            if category in ["Beverages", "Dairy", "Bakery", "Produce"]:
                cost = round(float(self.rng.uniform(0.80, 5.00)), 2)
                margin = float(self.rng.uniform(1.30, 1.80))
                volume = round(float(self.rng.uniform(0.001, 0.005)), 4)
                weight = round(float(self.rng.uniform(0.2, 2.0)), 2)
            elif category in ["Frozen", "Pantry"]:
                cost = round(float(self.rng.uniform(2.50, 12.00)), 2)
                margin = float(self.rng.uniform(1.35, 1.90))
                volume = round(float(self.rng.uniform(0.002, 0.010)), 4)
                weight = round(float(self.rng.uniform(0.5, 3.0)), 2)
            else:  # Personal Care, Household
                cost = round(float(self.rng.uniform(4.00, 25.00)), 2)
                margin = float(self.rng.uniform(1.50, 2.40))
                volume = round(float(self.rng.uniform(0.003, 0.015)), 4)
                weight = round(float(self.rng.uniform(0.3, 4.0)), 2)
            
            price = round(cost * margin, 2)

            # Product lifecycle status
            status_roll = self.rng.uniform(0, 1)
            launch_offset = self.rng.randint(0, max(1, self.profile.num_days // 4))
            launch_date = (self.start_date + timedelta(days=launch_offset)).strftime("%Y-%m-%d")
            
            if status_roll < 0.88:
                status = "ACTIVE"
                discontinue_date = None
            elif status_roll < 0.94:
                status = "PHASE_OUT"
                discontinue_offset = self.rng.randint(self.profile.num_days // 2, self.profile.num_days + 60)
                discontinue_date = (self.start_date + timedelta(days=discontinue_offset)).strftime("%Y-%m-%d")
            else:
                status = "DISCONTINUED"
                discontinue_offset = self.rng.randint(15, max(20, self.profile.num_days // 2))
                discontinue_date = (self.start_date + timedelta(days=discontinue_offset)).strftime("%Y-%m-%d")

            self.skus.append({
                "sku_id": sku_id,
                "sku_name": f"{category} Item {i:04d}",
                "category": category,
                "unit_cost": cost,
                "unit_price": price,
                "unit_volume_m3": volume,
                "unit_weight_kg": weight,
                "status": status,
                "launch_date": launch_date,
                "discontinue_date": discontinue_date,
            })

        # 2. Stores
        for j in range(1, self.profile.num_stores + 1):
            store_id = f"STORE-{j:06d}"
            channel = self.rng.choice(STORE_CHANNELS)
            region = self.rng.choice(STORE_REGIONS)
            
            if channel == "REGIONAL_DC":
                max_units = int(self.rng.randint(50000, 200000))
                max_vol = round(float(max_units * 0.008), 2)
                cadence = 1
            elif channel == "ECOMM_HUB":
                max_units = int(self.rng.randint(25000, 80000))
                max_vol = round(float(max_units * 0.007), 2)
                cadence = 1
            elif channel == "RETAIL_SUPERMARKET":
                max_units = int(self.rng.randint(10000, 40000))
                max_vol = round(float(max_units * 0.006), 2)
                cadence = int(self.rng.choice([1, 2]))
            else:  # CONVENIENCE
                max_units = int(self.rng.randint(3000, 10000))
                max_vol = round(float(max_units * 0.005), 2)
                cadence = int(self.rng.choice([2, 7]))

            open_date = (self.start_date - timedelta(days=self.rng.randint(300, 1500))).strftime("%Y-%m-%d")

            self.stores.append({
                "store_id": store_id,
                "store_name": f"{region} {channel.replace('_', ' ').title()} {j:03d}",
                "channel": channel,
                "region": region,
                "max_storage_units": max_units,
                "max_storage_volume_m3": max_vol,
                "replenishment_cadence_days": cadence,
                "opened_date": open_date,
            })

        # 3. Suppliers
        for k in range(1, self.profile.num_suppliers + 1):
            supp_id = f"SUPP-{k:04d}"
            tier = self.rng.choice(SUPPLIER_TIERS)
            reliability = round(float(self.rng.uniform(0.82, 0.99) if tier == "TIER_1" else self.rng.uniform(0.70, 0.92)), 2)
            payment_terms = int(self.rng.choice([30, 45, 60]))
            country = str(self.rng.choice(["US", "CA", "MX", "DE", "CN", "VN"]))

            self.suppliers.append({
                "supplier_id": supp_id,
                "supplier_name": f"Vendor Partner {k:03d} ({tier})",
                "tier": tier,
                "reliability_score": reliability,
                "payment_terms_days": payment_terms,
                "country": country,
            })

    def generate_supplier_sku_matrix(self):
        """Bridges Supplier and SKU (N:M) with pack size, MOQ, and lead time distribution."""
        supp_ids = [s["supplier_id"] for s in self.suppliers]

        for sku in self.skus:
            sku_id = sku["sku_id"]
            # Primary supplier
            prim_supp = self.rng.choice(supp_ids)
            pack_size = int(self.rng.choice([6, 12, 24, 48]))
            moq_mult = int(self.rng.choice([1, 2, 4, 5]))
            moq_units = pack_size * moq_mult
            lead_time = int(self.rng.randint(3, 14))
            lead_std = round(float(self.rng.uniform(0.5, 2.0)), 1)
            unit_cost = sku["unit_cost"]

            bridge_id = f"SSKU-{prim_supp}-{sku_id}"
            self.supplier_skus.append({
                "supplier_sku_id": bridge_id,
                "supplier_id": prim_supp,
                "sku_id": sku_id,
                "pack_size": pack_size,
                "moq_units": moq_units,
                "unit_purchase_cost": unit_cost,
                "nominal_lead_time_days": lead_time,
                "lead_time_std_days": lead_std,
                "is_primary": True,
                "effective_from": self.profile.start_date,
                "effective_to": None,
            })

            # Secondary supplier for 20% of SKUs
            if self.rng.uniform(0, 1) < 0.20:
                other_supps = [s for s in supp_ids if s != prim_supp]
                if other_supps:
                    sec_supp = self.rng.choice(other_supps)
                    sec_lead = max(2, lead_time + self.rng.randint(-1, 3))
                    sec_pack = pack_size
                    sec_bridge = f"SSKU-{sec_supp}-{sku_id}"
                    self.supplier_skus.append({
                        "supplier_sku_id": sec_bridge,
                        "supplier_id": sec_supp,
                        "sku_id": sku_id,
                        "pack_size": sec_pack,
                        "moq_units": sec_pack * max(1, moq_mult - 1),
                        "unit_purchase_cost": round(unit_cost * 1.05, 2),
                        "nominal_lead_time_days": sec_lead,
                        "lead_time_std_days": round(lead_std * 1.2, 1),
                        "is_primary": False,
                        "effective_from": self.profile.start_date,
                        "effective_to": None,
                    })

    def generate_sales_and_inventory_events(self):
        """Simulates daily demand, stockouts, deliveries, and inventory snapshots."""
        supp_sku_map = {
            s["sku_id"]: s for s in self.supplier_skus if s["is_primary"]
        }
        sku_dict = {s["sku_id"]: s for s in self.skus}
        
        # Day of week multiplier (Mon -> Sun)
        dow_multipliers = [0.90, 0.90, 0.95, 1.05, 1.25, 1.40, 1.15]
        
        po_counter = 0
        lto_counter = 0

        # Run per store-sku pair
        for store in self.stores:
            store_id = store["store_id"]

            for sku in self.skus:
                sku_id = sku["sku_id"]
                sku_info = sku_dict[sku_id]
                contract = supp_sku_map.get(sku_id)
                if not contract:
                    continue

                lead_time_nom = contract["nominal_lead_time_days"]
                lead_time_std = contract["lead_time_std_days"]
                pack_size = contract["pack_size"]
                moq = contract["moq_units"]
                unit_price = sku_info["unit_price"]

                # Velocity classification: fast (20%), medium (50%), intermittent slow (30%)
                vel_type = self.rng.choice(["FAST", "MEDIUM", "SLOW_INTERMITTENT"], p=[0.20, 0.50, 0.30])
                if vel_type == "FAST":
                    base_lambda = float(self.rng.uniform(12.0, 28.0))
                elif vel_type == "MEDIUM":
                    base_lambda = float(self.rng.uniform(3.0, 8.0))
                else:
                    base_lambda = float(self.rng.uniform(0.15, 0.85))

                # Safety stock and ROP baseline for simulation replenishment
                daily_std = math.sqrt(base_lambda) if base_lambda > 1.0 else 0.8
                ss_est = int(math.ceil(1.645 * math.sqrt(lead_time_nom * (daily_std ** 2) + (base_lambda ** 2) * (lead_time_std ** 2))))
                rop_est = int(math.ceil(base_lambda * lead_time_nom + ss_est))
                tsl_est = rop_est + int(math.ceil(base_lambda * 7))

                # Initial inventory state
                current_on_hand = int(max(rop_est, self.rng.randint(ss_est, tsl_est + 1)))
                current_on_order = 0
                pipeline_deliveries: Dict[str, int] = {}  # date_str -> qty

                # Simulate day by day
                for day_idx in range(self.profile.num_days):
                    current_dt = self.start_date + timedelta(days=day_idx)
                    date_str = current_dt.strftime("%Y-%m-%d")

                    # Check lifecycle bounds
                    if date_str < sku_info["launch_date"]:
                        continue
                    if sku_info["discontinue_date"] and date_str > sku_info["discontinue_date"]:
                        continue

                    # 1. Receive incoming shipments
                    delivered_qty = pipeline_deliveries.pop(date_str, 0)
                    opening_on_hand = current_on_hand
                    current_on_hand += delivered_qty
                    current_on_order = max(0, current_on_order - delivered_qty)

                    # 2. Demand generation with seasonality and promotions
                    dow = current_dt.weekday()
                    dow_factor = dow_multipliers[dow]
                    
                    # 5% probability of promotion
                    is_promo = bool(self.rng.uniform(0, 1) < 0.05)
                    promo_discount = round(float(self.rng.choice([0.10, 0.15, 0.20, 0.25])), 2) if is_promo else 0.0
                    promo_lift = 1.0 + (promo_discount * 3.0) if is_promo else 1.0

                    effective_lambda = base_lambda * dow_factor * promo_lift

                    if vel_type == "SLOW_INTERMITTENT":
                        has_sale = self.rng.uniform(0, 1) < min(0.8, effective_lambda)
                        unconstrained_demand = int(self.rng.randint(1, 4)) if has_sale else 0
                    else:
                        unconstrained_demand = int(self.rng.poisson(effective_lambda))

                    # 3. Fulfill sales vs stockout
                    if unconstrained_demand <= current_on_hand:
                        units_sold = unconstrained_demand
                        stockout_flag = False
                        lost_sales = 0.0
                    else:
                        units_sold = current_on_hand
                        stockout_flag = True
                        lost_sales = float(unconstrained_demand - units_sold)

                    closing_on_hand = current_on_hand - units_sold
                    current_on_hand = closing_on_hand

                    # Financials & derived fields
                    actual_price = round(unit_price * (1.0 - promo_discount), 2)
                    gross_revenue = round(units_sold * actual_price, 2)
                    reserved_qty = int(min(closing_on_hand, math.floor(closing_on_hand * 0.08)))
                    available_qty = max(0, closing_on_hand + current_on_order - reserved_qty)
                    avg_demand_denom = max(base_lambda, 0.05)
                    days_of_supply = round(available_qty / avg_demand_denom, 1)

                    # Append SalesHistory
                    sale_id = f"SALE-{store_id}-{sku_id}-{date_str}"
                    self.sales_history.append({
                        "sale_id": sale_id,
                        "store_id": store_id,
                        "sku_id": sku_id,
                        "date": date_str,
                        "units_sold": units_sold,
                        "promotion_flag": is_promo,
                        "promo_discount_pct": promo_discount,
                        "stockout_flag": stockout_flag,
                        "unconstrained_demand_est": float(unconstrained_demand),
                        "lost_sales_units": lost_sales,
                        "unit_selling_price": actual_price,
                        "gross_revenue": gross_revenue,
                    })

                    # Append InventorySnapshot
                    snapshot_id = f"INV-{store_id}-{sku_id}-{date_str}"
                    self.inventory_snapshots.append({
                        "snapshot_id": snapshot_id,
                        "store_id": store_id,
                        "sku_id": sku_id,
                        "date": date_str,
                        "opening_on_hand_qty": opening_on_hand,
                        "received_qty": delivered_qty,
                        "units_sold": units_sold,
                        "closing_on_hand_qty": closing_on_hand,
                        "on_order_qty": current_on_order,
                        "reserved_qty": reserved_qty,
                        "available_qty": available_qty,
                        "stockout_flag": bool(closing_on_hand == 0),
                        "days_of_supply": days_of_supply,
                    })

                    # 4. Pipeline Replenishment order trigger
                    inventory_position = closing_on_hand + current_on_order - reserved_qty
                    if inventory_position <= rop_est:
                        order_need = max(0, tsl_est - inventory_position)
                        order_qty_pre = max(order_need, moq)
                        order_qty = int(math.ceil(order_qty_pre / pack_size) * pack_size)

                        if order_qty > 0:
                            po_counter += 1
                            po_id = f"PO-2025-{po_counter:06d}"
                            
                            # Lead time realization
                            actual_lt = max(1, int(round(self.rng.normal(lead_time_nom, lead_time_std))))
                            arrival_dt = current_dt + timedelta(days=actual_lt)
                            arrival_str = arrival_dt.strftime("%Y-%m-%d")

                            # Track in pipeline
                            pipeline_deliveries[arrival_str] = pipeline_deliveries.get(arrival_str, 0) + order_qty
                            current_on_order += order_qty

                            # Record LeadTimeObservation upon delivery realization
                            lto_counter += 1
                            expected_dt = current_dt + timedelta(days=lead_time_nom)
                            lt_var = actual_lt - lead_time_nom
                            status = "ON_TIME" if lt_var == 0 else ("DELAYED" if lt_var > 0 else "EARLY")
                            delay_reason = "PORT_CONGESTION" if lt_var > 2 else ("WEATHER" if lt_var > 0 else "NONE")

                            self.lead_time_observations.append({
                                "observation_id": f"LTO-{lto_counter:06d}",
                                "po_id": po_id,
                                "supplier_id": contract["supplier_id"],
                                "sku_id": sku_id,
                                "order_date": date_str,
                                "expected_delivery_date": expected_dt.strftime("%Y-%m-%d"),
                                "actual_delivery_date": arrival_str,
                                "nominal_lead_time_days": lead_time_nom,
                                "actual_lead_time_days": actual_lt,
                                "lead_time_variance_days": lt_var,
                                "status": status,
                                "delay_reason": delay_reason,
                            })

    def generate_forecasts_and_policies(self):
        """Generates statistical demand forecasts and mathematically calculated ReorderPolicies."""
        sales_df = pd.DataFrame(self.sales_history)
        supp_sku_map = {s["sku_id"]: s for s in self.supplier_skus if s["is_primary"]}

        forecast_as_of = (self.start_date + timedelta(days=self.profile.num_days - 1)).strftime("%Y-%m-%d")
        horizon_start = (self.start_date + timedelta(days=self.profile.num_days)).strftime("%Y-%m-%d")
        horizon_end = (self.start_date + timedelta(days=self.profile.num_days + 14)).strftime("%Y-%m-%d")
        horizon_days = 14

        for store in self.stores:
            store_id = store["store_id"]
            
            for sku in self.skus:
                sku_id = sku["sku_id"]
                contract = supp_sku_map.get(sku_id)
                if not contract:
                    continue

                sku_sales = sales_df[(sales_df["store_id"] == store_id) & (sales_df["sku_id"] == sku_id)]
                if len(sku_sales) == 0:
                    continue

                # Uncensored demand estimation: uses unconstrained demand during stockouts
                mean_daily = float(sku_sales["unconstrained_demand_est"].mean())
                std_daily = float(sku_sales["unconstrained_demand_est"].std()) if len(sku_sales) > 1 else 0.5
                if math.isnan(std_daily) or std_daily < 0.1:
                    std_daily = 0.5

                # Forecasting method selection
                zero_ratio = float((sku_sales["units_sold"] == 0).mean())
                method = "CROSTON_INTERMITTENT" if zero_ratio > 0.45 else "HOLT_WINTERS"

                fc_id = f"FC-{store_id}-{sku_id}-{forecast_as_of[:7]}"
                total_horizon = round(mean_daily * horizon_days, 2)
                promo_factor = 1.0

                self.forecasts.append({
                    "forecast_id": fc_id,
                    "store_id": store_id,
                    "sku_id": sku_id,
                    "forecast_date": forecast_as_of,
                    "horizon_start_date": horizon_start,
                    "horizon_end_date": horizon_end,
                    "horizon_days": horizon_days,
                    "forecasted_daily_demand": round(mean_daily, 2),
                    "forecasted_daily_std": round(std_daily, 2),
                    "forecasted_total_horizon_demand": total_horizon,
                    "method": method,
                    "promo_uplift_factor": promo_factor,
                    "stockout_uncensored": True,
                    "created_at": f"{forecast_as_of}T00:00:00Z",
                })

                # Reorder Policy calculation
                # SS = Z * sqrt(L * sigma_d^2 + d^2 * sigma_L^2)
                service_level = 0.95
                z_factor = 1.645
                lead_time = float(contract["nominal_lead_time_days"])
                lead_std = float(contract["lead_time_std_days"])

                combined_var = (lead_time * (std_daily ** 2)) + ((mean_daily ** 2) * (lead_std ** 2))
                safety_stock = int(math.ceil(z_factor * math.sqrt(combined_var)))
                lead_time_demand = round(mean_daily * lead_time, 2)
                reorder_point = int(math.ceil(lead_time_demand + safety_stock))
                review_period = int(store["replenishment_cadence_days"])
                target_stock = int(math.ceil(reorder_point + (review_period * mean_daily)))
                max_capacity = int(store["max_storage_units"] // max(1, len(self.skus) // 2))

                policy_id = f"RP-{store_id}-{sku_id}"
                self.reorder_policies.append({
                    "policy_id": policy_id,
                    "store_id": store_id,
                    "sku_id": sku_id,
                    "service_level": service_level,
                    "z_factor": z_factor,
                    "effective_lead_time_days": lead_time,
                    "lead_time_demand": lead_time_demand,
                    "safety_stock_units": safety_stock,
                    "reorder_point_units": reorder_point,
                    "target_stock_level": target_stock,
                    "review_period_days": review_period,
                    "max_store_capacity_units": max_capacity,
                    "last_updated": forecast_as_of,
                })

    def generate_replenishment_decisions(self):
        """Generates purchase recommendations with multi-constraint logic (pack size, MOQ, capacity)."""
        inv_df = pd.DataFrame(self.inventory_snapshots)
        last_date = (self.start_date + timedelta(days=self.profile.num_days - 1)).strftime("%Y-%m-%d")
        latest_inv = inv_df[inv_df["date"] == last_date].set_index(["store_id", "sku_id"])

        supp_sku_map = {s["sku_id"]: s for s in self.supplier_skus if s["is_primary"]}
        policy_map = {(p["store_id"], p["sku_id"]): p for p in self.reorder_policies}
        sku_map = {s["sku_id"]: s for s in self.skus}
        store_map = {s["store_id"]: s for s in self.stores}

        rec_counter = 0

        for (store_id, sku_id), policy in policy_map.items():
            if (store_id, sku_id) not in latest_inv.index:
                continue

            inv_row = latest_inv.loc[(store_id, sku_id)]
            on_hand = int(inv_row["closing_on_hand_qty"])
            on_order = int(inv_row["on_order_qty"])
            reserved = int(inv_row["reserved_qty"])
            inventory_position = on_hand + on_order - reserved

            rop = int(policy["reorder_point_units"])
            tsl = int(policy["target_stock_level"])
            max_cap = int(policy["max_store_capacity_units"])
            contract = supp_sku_map[sku_id]
            pack_size = int(contract["pack_size"])
            moq = int(contract["moq_units"])
            unit_cost = float(contract["unit_purchase_cost"])
            sku_info = sku_map[sku_id]

            # Reorder trigger evaluation
            if inventory_position <= rop:
                rec_counter += 1
                rec_id = f"PO-2026-{rec_counter:06d}"
                gross_need = max(0, tsl - inventory_position)
                unrounded_need = max(gross_need, moq) if gross_need > 0 else 0
                
                # Apply pack size rounding
                pack_rounded_qty = int(math.ceil(unrounded_need / pack_size) * pack_size)

                # Apply capacity constraint
                capacity_allowed = max(0, max_cap - inventory_position)
                if pack_rounded_qty > capacity_allowed:
                    # Constrained by store backroom/shelf capacity
                    final_qty = max(0, (capacity_allowed // pack_size) * pack_size)
                    exception_code = "ERR_CAPACITY_EXCEEDED"
                    status = "EXCEPTION_FLAGGED"
                    rationale = f"Order truncated from {pack_rounded_qty} to {final_qty} due to store shelf capacity limit ({max_cap} units)."
                else:
                    final_qty = pack_rounded_qty
                    exception_code = "NONE"
                    status = "RECOMMENDED"
                    rationale = f"Net position {inventory_position} <= ROP {rop}. Replenishing to TSL {tsl} with MOQ {moq} and pack size {pack_size}."

                # Discontinued product check
                if sku_info["status"] == "DISCONTINUED":
                    final_qty = 0
                    exception_code = "ERR_DISCONTINUED_SKU"
                    status = "REJECTED"
                    rationale = f"Replenishment halted: SKU {sku_id} is discontinued."

                # Priority assignment
                if on_hand == 0:
                    priority = "CRITICAL_STOCKOUT"
                elif inventory_position < policy["safety_stock_units"]:
                    priority = "HIGH_RISK"
                else:
                    priority = "ROUTINE"

                total_cost = round(final_qty * unit_cost, 2)

                self.purchase_recommendations.append({
                    "recommendation_id": rec_id,
                    "store_id": store_id,
                    "sku_id": sku_id,
                    "supplier_id": contract["supplier_id"],
                    "recommendation_date": last_date,
                    "current_on_hand_qty": on_hand,
                    "current_on_order_qty": on_order,
                    "current_reserved_qty": reserved,
                    "net_inventory_position": inventory_position,
                    "reorder_point": rop,
                    "target_stock_level": tsl,
                    "gross_need_units": gross_need,
                    "unrounded_order_qty": unrounded_need,
                    "pack_size_applied": pack_size,
                    "moq_applied": moq,
                    "capacity_constrained_qty": pack_rounded_qty if final_qty == pack_rounded_qty else final_qty,
                    "final_order_qty": final_qty,
                    "unit_cost": unit_cost,
                    "total_cost": total_cost,
                    "priority": priority,
                    "status": status,
                    "exception_code": exception_code,
                    "rationale": rationale,
                    "created_at": f"{last_date}T08:00:00Z",
                })

    def generate_lifecycle_audit_events(self):
        """Preserves full audit trail of order recommendations and state transitions."""
        evt_counter = 0

        for rec in self.purchase_recommendations:
            rec_id = rec["recommendation_id"]
            rec_date = rec["recommendation_date"]

            # Event 1: Initial recommendation generated by system
            evt_counter += 1
            self.order_lifecycle_events.append({
                "event_id": f"EVT-{evt_counter:06d}",
                "recommendation_id": rec_id,
                "from_status": "NONE",
                "to_status": rec["status"],
                "actor": "System/ReplenishmentEngine",
                "action": "GENERATE",
                "notes": f"Algorithmic recommendation generated. Exception: {rec['exception_code']}",
                "timestamp": f"{rec_date}T08:00:00Z",
            })

            # Event 2: Operator / Analyst action
            if rec["status"] == "RECOMMENDED":
                evt_counter += 1
                self.order_lifecycle_events.append({
                    "event_id": f"EVT-{evt_counter:06d}",
                    "recommendation_id": rec_id,
                    "from_status": "RECOMMENDED",
                    "to_status": "APPROVED",
                    "actor": "OperationsManager",
                    "action": "APPROVE",
                    "notes": "Reviewed and approved for dispatch to vendor.",
                    "timestamp": f"{rec_date}T10:15:00Z",
                })
            elif rec["status"] == "EXCEPTION_FLAGGED":
                evt_counter += 1
                self.order_lifecycle_events.append({
                    "event_id": f"EVT-{evt_counter:06d}",
                    "recommendation_id": rec_id,
                    "from_status": "EXCEPTION_FLAGGED",
                    "to_status": "EXCEPTION_FLAGGED",
                    "actor": "StoreManager",
                    "action": "ESCALATE",
                    "notes": f"Escalated to inventory controller: {rec['rationale']}",
                    "timestamp": f"{rec_date}T09:30:00Z",
                })

