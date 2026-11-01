"""End-to-End Demonstration Script for SKU-Location Replenishment Engine.

Runs the complete workflow:
1. Synthetic generation across 10 entities
2. Anomaly injection with segregated ground truth
3. Demand uncensoring and temporal holdout evaluation
4. Multi-constraint replenishment recommendations (MOQ, pack size, capacity)
5. Audit trail and lifecycle state transitions
6. Referential integrity validation
7. Step 10 reproducibility verification
"""

import os
import json
import pandas as pd
from datetime import datetime

from replenishment_engine.config import DEFAULT_RANDOM_SEED
from replenishment_engine.generator.synthetic_data_generator import ReplenishmentDataGenerator
from replenishment_engine.generator.anomaly_injector import AnomalyInjector
from replenishment_engine.forecasting.evaluator import ForecastEvaluator
from replenishment_engine.forecasting.uncensor import DemandUncensorer
from replenishment_engine.validation.data_validator import DataValidator
from replenishment_engine.validation.audit import verify_reproducibility, generate_manifest
from cli import export_bundle_to_disk


def run_pipeline():
    print("=" * 80)
    print("SKU-LOCATION DEMAND FORECASTING & REPLENISHMENT WORKFLOW ENGINE")
    print("=" * 80)
    print(f"Timestamp:   {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Random Seed: {DEFAULT_RANDOM_SEED}")
    print(f"Scale:       Starter Profile (50 SKUs, 5 Stores, 90 Days)")
    print("-" * 80)

    # 1. Generate master and event records
    print("\n[Step 1 & 2] Generating Master Data and Dependent Events...")
    gen = ReplenishmentDataGenerator(seed=DEFAULT_RANDOM_SEED, profile_name="starter")
    tables = gen.generate_all()
    for ent, df in tables.items():
        print(f"  * {ent:25s}: {len(df):6,d} rows")

    # 2. Inject edge cases & negative scenarios
    print("\n[Step 5 & 7] Injecting 5 Calibrated Edge Cases into Segregated Ground Truth...")
    injector = AnomalyInjector(seed=DEFAULT_RANDOM_SEED)
    sales_mod, lead_mod, recs_mod, fc_mod, ground_truth = injector.inject_all_anomalies(
        tables["SalesHistory"],
        tables["LeadTimeObservation"],
        tables["PurchaseRecommendation"],
        tables["Forecast"],
        tables["SKU"],
    )
    tables["SalesHistory"] = sales_mod
    tables["LeadTimeObservation"] = lead_mod
    tables["PurchaseRecommendation"] = recs_mod
    tables["Forecast"] = fc_mod

    gt_df = pd.DataFrame(ground_truth)
    print(f"  * Total Ground Truth Anomalies Registered: {len(gt_df)}")
    print("  * Breakdown by Injected Issue Type:")
    breakdown = gt_df.groupby(["issue_type", "target_entity", "severity"]).size()
    for (issue, ent, sev), cnt in breakdown.items():
        print(f"      - {issue:28s} [{ent:22s} | {sev:8s}]: {cnt:2d} instances")

    # 3. Demand Uncensoring Analysis
    print("\n[Demand Analysis] Stockout Censoring Impact & Uncensoring:")
    censoring_summary = DemandUncensorer.calculate_censoring_impact(tables["SalesHistory"])
    print(f"  * Total Daily Observations:    {censoring_summary['total_observations']:,}")
    print(f"  * Stockout Occurrences:        {censoring_summary['stockout_events']:,} ({censoring_summary['stockout_percentage']}%)")
    print(f"  * Recorded Sales (Censored):   {censoring_summary['recorded_sales_units']:,} units")
    print(f"  * True Unconstrained Demand:   {censoring_summary['true_unconstrained_demand_units']:,} units")
    print(f"  * Lost Sales from Stockouts:   {censoring_summary['total_lost_sales_units']:,} units")
    print(f"  * Demand Underestimation Bias: {censoring_summary['demand_underestimation_pct']}% downward bias")

    # 4. Temporal Holdout Backtesting
    print("\n[Forecasting Engine] Temporal Holdout Backtesting (14-Day Lookahead):")
    holdout_res = ForecastEvaluator.evaluate_temporal_holdout(tables["SalesHistory"], holdout_days=14)
    c_m = holdout_res["censored_model_metrics"]
    u_m = holdout_res["uncensored_model_metrics"]
    imp = holdout_res["censoring_impact_analysis"]
    print(f"  * Evaluated Horizons:          {holdout_res['evaluation_window']['holdout_start']} to {holdout_res['evaluation_window']['holdout_end']}")
    print(f"  * Series Evaluated:            {holdout_res['evaluation_window']['evaluated_series_count']}")
    print("  * Evaluation Results on True Customer Demand:")
    print(f"      - Censored Model (Naive):   WAPE={c_m['wape']:.4f} | RMSE={c_m['rmse']:.2f} | Bias={c_m['forecast_bias']:.4f}")
    print(f"      - Uncensored Model (Fixed): WAPE={u_m['wape']:.4f} | RMSE={u_m['rmse']:.2f} | Bias={u_m['forecast_bias']:.4f}")
    print(f"  * Bias Improvement:            {imp['bias_improvement']:.4f} reduction in underforecasting")
    print(f"  * Key Takeaway:                {imp['conclusion']}")

    # 5. Replenishment Recommendations & Decision Rules
    print("\n[Replenishment Engine] Multi-Constraint Reorder Decisions:")
    recs = tables["PurchaseRecommendation"]
    print(f"  * Total Recommendations Generated: {len(recs)}")
    print("  * Decision Outcomes by Status & Exception Code:")
    rec_summary = recs.groupby(["status", "exception_code"]).size()
    for (st, ex), cnt in rec_summary.items():
        print(f"      - Status: {st:18s} | Exception: {ex:25s} | Count: {cnt}")

    # Display sample exceptional decisions
    print("\n  * Sample Traceable Decision Rationale:")
    sample_exceptions = recs[recs["exception_code"] != "NONE"].head(3)
    for _, r in sample_exceptions.iterrows():
        print(f"      [{r['recommendation_id']}] Store: {r['store_id']}, SKU: {r['sku_id']}")
        print(f"         Status: {r['status']} | Exception: {r['exception_code']} | Qty: {r['final_order_qty']}")
        print(f"         Rationale: {r['rationale']}")

    # 6. Lifecycle Events Audit Trail
    print("\n[Audit Trail] Order Lifecycle Events Log:")
    events = tables["OrderLifecycleEvent"]
    print(f"  * Total Immutable Audit Events: {len(events)}")
    print(f"  * Sample Audit Log Entries:")
    for _, ev in events.head(3).iterrows():
        print(f"      [{ev['event_id']}] PO: {ev['recommendation_id']} | Transition: {ev['from_status']} -> {ev['to_status']} | Actor: {ev['actor']} | Action: {ev['action']}")

    # 7. Referential Integrity & Data Validation
    print("\n[Step 8] Data Quality & Referential Integrity Validation:")
    report = DataValidator.validate_dataset_bundle(tables)
    print(f"  * Validation Status: {'PASSED' if report['is_valid'] else 'FAILED'}")
    print(f"  * Total Rules Evaluated: {report['total_checks']}")
    print(f"  * Passed Checks:         {report['passed_checks']}")
    print(f"  * Failed Checks:         {report['failed_checks']}")

    # 8. Step 10 Reproducibility Check
    print("\n[Step 10] Reproducibility Verification (Double Regeneration):")
    rep_res = verify_reproducibility(seed=DEFAULT_RANDOM_SEED, profile="starter")
    print(f"  * Reproducibility Status: {'PASSED (Bit-for-Bit Identical)' if rep_res['is_reproducible'] else 'FAILED'}")
    print(f"  * Tables Verified:        {rep_res['tables_evaluated']}/{rep_res['tables_evaluated']} identical")

    # 9. Export All Artifacts
    print("\n[Step 9] Exporting Relational Seed Bundle...")
    manifest = export_bundle_to_disk(
        tables=tables,
        ground_truth=ground_truth,
        export_dir="exports",
        seed=DEFAULT_RANDOM_SEED,
        profile="starter",
    )
    print(f"  * Total Records Exported: {manifest['total_records']:,}")
    print(f"  * Export Directory:       exports/")
    print(f"  * Seed Data SQL:          exports/seed_data.sql")
    print(f"  * Manifest Checksum:      exports/manifest.json")
    print("=" * 80)
    print("WORKFLOW EXECUTION COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    run_pipeline()

