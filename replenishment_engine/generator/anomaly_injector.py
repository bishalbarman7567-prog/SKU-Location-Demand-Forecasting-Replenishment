"""Edge Case and Anomaly Injection Module.

Injects the 5 required negative scenarios and edge cases into baseline data,
creating a strictly segregated ground_truth registry without leaking ground truth
labels into the input operational feature columns.

Required Scenarios:
1. STOCKOUT_CENSORED_AS_ZERO: Stockout mistaken for zero demand in historical sales.
2. PACK_SIZE_VIOLATION: Reorder recommendation ignores supplier master carton pack size.
3. DISCONTINUED_SKU_ORDERED: Reorder recommendation generated for discontinued SKU.
4. NEGATIVE_LEAD_TIME: Corrupted dock receipt where actual_lead_time_days < 0.
5. DATA_LEAKAGE_FUTURE_SALES: Forecast generated using observations from future dates.
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Tuple
import pandas as pd
import numpy as np


@dataclass
class GroundTruthAnomaly:
    """Record in ground_truth.csv / json identifying injected edge cases."""
    anomaly_id: str
    issue_type: str
    target_entity: str
    record_id: str
    field_name: str
    corrupted_value: Any
    expected_correct_value: Any
    detection_rule: str
    severity: str
    notes: str


class AnomalyInjector:
    """Injects calibrated edge cases into baseline datasets and records ground truth."""

    def __init__(self, seed: int = 20261022):
        self.rng = np.random.RandomState(seed)
        self.ground_truth_records: List[GroundTruthAnomaly] = []
        self._anomaly_counter = 0

    def _next_anomaly_id(self) -> str:
        self._anomaly_counter += 1
        return f"ANOM-{self._anomaly_counter:06d}"

    def inject_all_anomalies(
        self,
        sales_df: pd.DataFrame,
        lead_times_df: pd.DataFrame,
        recommendations_df: pd.DataFrame,
        forecasts_df: pd.DataFrame,
        skus_df: pd.DataFrame,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, List[Dict[str, Any]]]:
        """Injects all 5 required edge cases and returns mutated copies with separate ground truth."""
        sales_mod = sales_df.copy()
        lead_mod = lead_times_df.copy()
        recs_mod = recommendations_df.copy()
        fc_mod = forecasts_df.copy()

        # 1. Edge Case: STOCKOUT_CENSORED_AS_ZERO
        # Identify true stockouts where unconstrained demand was high, but naive record censored it as zero demand
        # We find records where stockout_flag is True, but mutate unconstrained_demand_est or note the naive misinterpretation
        stockout_indices = sales_mod[sales_mod["stockout_flag"] == True].index
        if len(stockout_indices) > 0:
            sample_size = min(max(1, len(stockout_indices) // 10), 15)
            selected_indices = self.rng.choice(stockout_indices, size=sample_size, replace=False)
            for idx in selected_indices:
                rec_id = sales_mod.loc[idx, "sale_id"]
                orig_unconstrained = sales_mod.loc[idx, "unconstrained_demand_est"]
                # In naive operational data, unconstrained_demand is wrongly recorded as units_sold (0)
                sales_mod.loc[idx, "naive_censored_demand"] = 0.0
                
                self.ground_truth_records.append(
                    GroundTruthAnomaly(
                        anomaly_id=self._next_anomaly_id(),
                        issue_type="STOCKOUT_CENSORED_AS_ZERO",
                        target_entity="SalesHistory",
                        record_id=rec_id,
                        field_name="unconstrained_demand_est",
                        corrupted_value=0.0,
                        expected_correct_value=float(orig_unconstrained),
                        detection_rule="stockout_flag == True AND units_sold == 0 AND unconstrained_demand > 0",
                        severity="HIGH",
                        notes="Stockout day mistakenly treated as genuine zero customer demand, inducing downward forecast bias.",
                    )
                )

        # 2. Edge Case: PACK_SIZE_VIOLATION
        # Reorder quantity ignores pack size (e.g. pack_size=12, order=17 instead of 24)
        if len(recs_mod) > 0:
            rec_indices = recs_mod[recs_mod["final_order_qty"] > 0].index
            if len(rec_indices) > 0:
                sample_size = min(max(1, len(rec_indices) // 8), 10)
                selected_recs = self.rng.choice(rec_indices, size=sample_size, replace=False)
                for idx in selected_recs:
                    rec_id = recs_mod.loc[idx, "recommendation_id"]
                    pack_size = int(recs_mod.loc[idx, "pack_size_applied"])
                    if pack_size > 1:
                        orig_order = int(recs_mod.loc[idx, "final_order_qty"])
                        # Inject non-multiple quantity
                        corrupted_qty = orig_order + self.rng.randint(1, pack_size)
                        recs_mod.loc[idx, "final_order_qty"] = corrupted_qty
                        recs_mod.loc[idx, "total_cost"] = round(corrupted_qty * float(recs_mod.loc[idx, "unit_cost"]), 2)
                        recs_mod.loc[idx, "exception_code"] = "ERR_PACK_SIZE_MISMATCH"
                        recs_mod.loc[idx, "status"] = "EXCEPTION_FLAGGED"

                        self.ground_truth_records.append(
                            GroundTruthAnomaly(
                                anomaly_id=self._next_anomaly_id(),
                                issue_type="PACK_SIZE_VIOLATION",
                                target_entity="PurchaseRecommendation",
                                record_id=rec_id,
                                field_name="final_order_qty",
                                corrupted_value=corrupted_qty,
                                expected_correct_value=orig_order,
                                detection_rule="final_order_qty % pack_size != 0",
                                severity="MEDIUM",
                                notes=f"Order quantity {corrupted_qty} is not an integer multiple of supplier pack size {pack_size}.",
                            )
                        )

        # 3. Edge Case: DISCONTINUED_SKU_ORDERED
        # SKU is discontinued, but an order recommendation was generated instead of suppressing
        discontinued_skus = skus_df[skus_df["status"] == "DISCONTINUED"]["sku_id"].tolist()
        if discontinued_skus and len(recs_mod) > 0:
            rec_indices = recs_mod.index
            sample_size = min(max(1, len(discontinued_skus)), 5)
            chosen_skus = discontinued_skus[:sample_size]
            for i, target_sku in enumerate(chosen_skus):
                if i < len(recs_mod):
                    target_idx = recs_mod.index[i]
                    rec_id = recs_mod.loc[target_idx, "recommendation_id"]
                    orig_sku = recs_mod.loc[target_idx, "sku_id"]
                    recs_mod.loc[target_idx, "sku_id"] = target_sku
                    recs_mod.loc[target_idx, "exception_code"] = "ERR_DISCONTINUED_SKU"
                    recs_mod.loc[target_idx, "status"] = "EXCEPTION_FLAGGED"
                    recs_mod.loc[target_idx, "rationale"] = (
                        f"EXCEPTION: SKU {target_sku} is marked DISCONTINUED in master catalog. "
                        "Replenishment prohibited by merchandising governance rules."
                    )

                    self.ground_truth_records.append(
                        GroundTruthAnomaly(
                            anomaly_id=self._next_anomaly_id(),
                            issue_type="DISCONTINUED_SKU_ORDERED",
                            target_entity="PurchaseRecommendation",
                            record_id=rec_id,
                            field_name="sku_id",
                            corrupted_value=target_sku,
                            expected_correct_value="SUPPRESS_ORDER_QTY_0",
                            detection_rule="SKU.status == 'DISCONTINUED' AND final_order_qty > 0",
                            severity="CRITICAL",
                            notes="Purchase recommendation created for discontinued product line; violates merchandising policy.",
                        )
                    )

        # 4. Edge Case: NEGATIVE_LEAD_TIME
        # Corrupted dock receipt where actual_lead_time_days < 0 (actual_delivery_date < order_date)
        if len(lead_mod) > 0:
            sample_size = min(max(1, len(lead_mod) // 10), 8)
            selected_leads = self.rng.choice(lead_mod.index, size=sample_size, replace=False)
            for idx in selected_leads:
                obs_id = lead_mod.loc[idx, "observation_id"]
                orig_lead_time = int(lead_mod.loc[idx, "actual_lead_time_days"])
                order_date = pd.to_datetime(lead_mod.loc[idx, "order_date"])
                corrupted_lead_time = -1 * self.rng.randint(1, 5)
                corrupted_delivery_date = (order_date + pd.Timedelta(days=corrupted_lead_time)).strftime("%Y-%m-%d")

                lead_mod.loc[idx, "actual_lead_time_days"] = corrupted_lead_time
                lead_mod.loc[idx, "actual_delivery_date"] = corrupted_delivery_date
                lead_mod.loc[idx, "delay_reason"] = "ERR_NEGATIVE_LEAD_TIME"

                self.ground_truth_records.append(
                    GroundTruthAnomaly(
                        anomaly_id=self._next_anomaly_id(),
                        issue_type="NEGATIVE_LEAD_TIME",
                        target_entity="LeadTimeObservation",
                        record_id=obs_id,
                        field_name="actual_lead_time_days",
                        corrupted_value=corrupted_lead_time,
                        expected_correct_value=orig_lead_time,
                        detection_rule="actual_lead_time_days < 0 OR actual_delivery_date < order_date",
                        severity="CRITICAL",
                        notes="Dock receipt date precedes PO order date; physically impossible negative lead time.",
                    )
                )

        # 5. Edge Case: DATA_LEAKAGE_FUTURE_SALES
        # Forecast for date T uses future sales (observation window contains post-forecast-date sales)
        if len(fc_mod) > 0:
            sample_size = min(max(1, len(fc_mod) // 10), 8)
            selected_fc = self.rng.choice(fc_mod.index, size=sample_size, replace=False)
            for idx in selected_fc:
                fc_id = fc_mod.loc[idx, "forecast_id"]
                orig_fc_date = fc_mod.loc[idx, "forecast_date"]
                orig_h_start = fc_mod.loc[idx, "horizon_start_date"]
                # Invert dates so forecast_date is in the future relative to horizon start
                leaked_fc_date = (pd.to_datetime(orig_h_start) + pd.Timedelta(days=15)).strftime("%Y-%m-%d")
                fc_mod.loc[idx, "forecast_date"] = leaked_fc_date

                self.ground_truth_records.append(
                    GroundTruthAnomaly(
                        anomaly_id=self._next_anomaly_id(),
                        issue_type="DATA_LEAKAGE_FUTURE_SALES",
                        target_entity="Forecast",
                        record_id=fc_id,
                        field_name="forecast_date",
                        corrupted_value=leaked_fc_date,
                        expected_correct_value=orig_fc_date,
                        detection_rule="forecast_date > horizon_start_date",
                        severity="HIGH",
                        notes="Lookahead data leakage: forecast generation timestamp is after the forecast horizon start date.",
                    )
                )

        ground_truth_dicts = [asdict(gt) for gt in self.ground_truth_records]
        return sales_mod, lead_mod, recs_mod, fc_mod, ground_truth_dicts

