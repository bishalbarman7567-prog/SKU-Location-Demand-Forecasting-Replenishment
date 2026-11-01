"""Command-Line Interface for SKU-Location Replenishment Engine.

Supports:
- generate: Deterministic synthetic generation with scale profiles and fixed seed
- forecast: Temporal holdout forecasting, uncensoring, and evaluation metrics
- replenish: Multi-constraint replenishment decisions, pack size/MOQ, and lifecycle events
- validate: Referential integrity, enum validation, arithmetic reconciliation
- reproduce: Step 10 acceptance check verifying bit-for-bit reproducibility
- run-all: Complete end-to-end execution and full artifact generation
"""

import argparse
import os
import sys
import json
from typing import Dict, Any
import pandas as pd

from replenishment_engine.config import DEFAULT_RANDOM_SEED, SCALE_PROFILES
from replenishment_engine.schemas.data_dictionary import (
    DATA_DICTIONARY,
    export_data_dictionary_markdown,
    export_data_dictionary_json,
)
from replenishment_engine.schemas.sql_ddl import generate_sql_ddl
from replenishment_engine.generator.synthetic_data_generator import ReplenishmentDataGenerator
from replenishment_engine.generator.anomaly_injector import AnomalyInjector
from replenishment_engine.forecasting.evaluator import ForecastEvaluator
from replenishment_engine.validation.data_validator import DataValidator
from replenishment_engine.validation.audit import generate_manifest, verify_reproducibility


def export_bundle_to_disk(
    tables: Dict[str, pd.DataFrame],
    ground_truth: list,
    export_dir: str,
    seed: int,
    profile: str,
) -> Dict[str, Any]:
    """Saves all tables as CSV, JSON, and SQL seed files, plus manifest and data dictionary."""
    os.makedirs(export_dir, exist_ok=True)

    # 1. Export CSVs
    csv_paths = {}
    for name, df in tables.items():
        tbl_file = DATA_DICTIONARY[name].table_name if name in DATA_DICTIONARY else name.lower()
        path = os.path.join(export_dir, f"{tbl_file}.csv")
        df.to_csv(path, index=False)
        csv_paths[name] = path

    # 2. Export Ground Truth CSV & JSON
    gt_df = pd.DataFrame(ground_truth)
    gt_csv_path = os.path.join(export_dir, "ground_truth.csv")
    gt_json_path = os.path.join(export_dir, "ground_truth.json")
    gt_df.to_csv(gt_csv_path, index=False)
    with open(gt_json_path, "w", encoding="utf-8") as f:
        json.dump(ground_truth, f, indent=2)

    # 3. Export Data Dictionary Markdown & JSON
    dd_md_path = os.path.join(export_dir, "data_dictionary.md")
    dd_json_path = os.path.join(export_dir, "data_dictionary.json")
    with open(dd_md_path, "w", encoding="utf-8") as f:
        f.write(export_data_dictionary_markdown())
    with open(dd_json_path, "w", encoding="utf-8") as f:
        f.write(export_data_dictionary_json())

    # 4. Export SQL Schema & Seed Data
    sql_path = os.path.join(export_dir, "seed_data.sql")
    ddl_sql = generate_sql_ddl()
    with open(sql_path, "w", encoding="utf-8") as f:
        f.write(ddl_sql)
        f.write("\n-- ============================================================================\n")
        f.write("-- Seed Insert Statements\n")
        f.write("-- ============================================================================\n\n")
        # Write inserts for master entities
        for name in ["SKU", "Store", "Supplier", "SupplierSKU"]:
            df = tables[name]
            tbl_name = DATA_DICTIONARY[name].table_name
            f.write(f"-- Inserts for {tbl_name}\n")
            for _, row in df.iterrows():
                cols = ", ".join(row.index)
                vals = []
                for v in row.values:
                    if pd.isnull(v) or v is None:
                        vals.append("NULL")
                    elif isinstance(v, (int, float, bool)):
                        vals.append(str(v).upper() if isinstance(v, bool) else str(v))
                    else:
                        escaped = str(v).replace("'", "''")
                        vals.append(f"'{escaped}'")
                f.write(f"INSERT INTO {tbl_name} ({cols}) VALUES ({', '.join(vals)});\n")
            f.write("\n")

    # 5. Manifest
    manifest = generate_manifest(tables, seed=seed, profile=profile)
    manifest_path = os.path.join(export_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return manifest


def cmd_generate(args):
    """Executes synthetic data generation and export."""
    print(f"[*] Initializing generator with seed={args.seed}, profile={args.profile}...")
    gen = ReplenishmentDataGenerator(seed=args.seed, profile_name=args.profile)
    tables = gen.generate_all()

    ground_truth = []
    if args.inject_anomalies:
        print("[*] Injecting 5 labelled edge cases into separate ground truth registry...")
        injector = AnomalyInjector(seed=args.seed)
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

    manifest = export_bundle_to_disk(
        tables=tables,
        ground_truth=ground_truth,
        export_dir=args.export_dir,
        seed=args.seed,
        profile=args.profile,
    )
    print(f"[+] Successfully exported {manifest['total_records']:,} records across {manifest['total_entities']} tables to '{args.export_dir}'.")
    for tbl_name, info in manifest["tables"].items():
        print(f"    - {tbl_name:25s}: {info['row_count']:8,d} rows | SHA256: {info['sha256_checksum'][:12]}...")


def cmd_forecast(args):
    """Evaluates temporal holdout demand forecasts."""
    sales_path = os.path.join(args.data_dir, "sales_history.csv")
    if not os.path.exists(sales_path):
        print(f"Error: Could not find {sales_path}. Run generate first.")
        sys.exit(1)

    print(f"[*] Loading sales history from {sales_path}...")
    sales_df = pd.read_csv(sales_path)
    print(f"[*] Running temporal holdout backtest (holdout_days={args.holdout_days})...")
    eval_res = ForecastEvaluator.evaluate_temporal_holdout(sales_df, holdout_days=args.holdout_days)

    out_path = args.export_file or os.path.join(args.data_dir, "forecast_evaluation.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(eval_res, f, indent=2)

    print(f"[+] Forecast evaluation completed. Results written to {out_path}.")
    print("\n--- Model Performance on True Customer Demand ---")
    c = eval_res["censored_model_metrics"]
    u = eval_res["uncensored_model_metrics"]
    print(f"  Naive Censored Model   | WAPE: {c['wape']:.4f} | RMSE: {c['rmse']:.2f} | Bias: {c['forecast_bias']:.4f}")
    print(f"  Uncensored Model       | WAPE: {u['wape']:.4f} | RMSE: {u['rmse']:.2f} | Bias: {u['forecast_bias']:.4f}")
    impact = eval_res["censoring_impact_analysis"]
    print(f"  Stockout Underforecast Gap: {impact['underforecast_gap_units']} units")
    print(f"  Bias Improvement:          {impact['bias_improvement']:.4f}")


def cmd_validate(args):
    """Audits data quality and referential integrity."""
    tables = {}
    for name, entity in DATA_DICTIONARY.items():
        csv_file = os.path.join(args.data_dir, f"{entity.table_name}.csv")
        if os.path.exists(csv_file):
            tables[name] = pd.read_csv(csv_file)

    if not tables:
        print(f"Error: No data tables found in {args.data_dir}. Run generate first.")
        sys.exit(1)

    print(f"[*] Validating {len(tables)} tables from {args.data_dir}...")
    report = DataValidator.validate_dataset_bundle(tables)

    out_path = args.export_file or os.path.join(args.data_dir, "validation_report.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    status_str = "PASSED" if report["is_valid"] else "FAILED"
    print(f"\n[+] Validation Status: {status_str}")
    print(f"    Total Checks:  {report['total_checks']}")
    print(f"    Passed Checks: {report['passed_checks']}")
    print(f"    Failed Checks: {report['failed_checks']}")
    if report["failures"]:
        print("\nFailures:")
        for fail in report["failures"]:
            print(f"    - {fail['check']}: {fail['error']}")
    print(f"Full validation report saved to {out_path}.")


def cmd_reproduce(args):
    """Executes Step 10 reproducibility verification."""
    print(f"[*] Running Step 10 reproducibility verification with seed={args.seed}, profile={args.profile}...")
    res = verify_reproducibility(seed=args.seed, profile=args.profile)
    status_str = "PASSED (100% Bit-for-Bit Match)" if res["is_reproducible"] else "FAILED"
    print(f"\n[+] Step 10 Reproducibility Status: {status_str}")
    for tbl, det in res["table_details"].items():
        match_str = "MATCH" if det["bit_for_bit_identical"] else "MISMATCH"
        print(f"    {tbl:25s} | Run1: {det['run_1_rows']:6d} | Run2: {det['run_2_rows']:6d} | [{match_str}]")


def cmd_run_all(args):
    """Runs complete end-to-end pipeline."""
    cmd_generate(args)
    cmd_forecast(args)
    cmd_validate(args)
    cmd_reproduce(args)


def main():
    parser = argparse.ArgumentParser(description="SKU-Location Demand Forecasting & Replenishment CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: generate
    p_gen = subparsers.add_parser("generate", help="Generate synthetic data")
    p_gen.add_argument("--seed", type=int, default=DEFAULT_RANDOM_SEED, help="Random seed")
    p_gen.add_argument("--profile", type=str, default="starter", choices=["starter", "medium", "full"], help="Scale profile")
    p_gen.add_argument("--export-dir", type=str, default="exports", help="Target export directory")
    p_gen.add_argument("--inject-anomalies", action="store_true", default=True, help="Inject 5 labelled edge cases")
    p_gen.set_defaults(func=cmd_generate)

    # Subcommand: forecast
    p_fc = subparsers.add_parser("forecast", help="Run forecast holdout backtesting")
    p_fc.add_argument("--data-dir", type=str, default="exports", help="Directory with sales data")
    p_fc.add_argument("--holdout-days", type=int, default=14, help="Holdout evaluation window days")
    p_fc.add_argument("--export-file", type=str, default=None, help="Output JSON path")
    p_fc.set_defaults(func=cmd_forecast)

    # Subcommand: validate
    p_val = subparsers.add_parser("validate", help="Validate relational integrity and rules")
    p_val.add_argument("--data-dir", type=str, default="exports", help="Directory with data files")
    p_val.add_argument("--export-file", type=str, default=None, help="Output JSON path")
    p_val.set_defaults(func=cmd_validate)

    # Subcommand: reproduce
    p_rep = subparsers.add_parser("reproduce", help="Run Step 10 reproducibility check")
    p_rep.add_argument("--seed", type=int, default=DEFAULT_RANDOM_SEED, help="Random seed")
    p_rep.add_argument("--profile", type=str, default="starter", choices=["starter", "medium", "full"], help="Scale profile")
    p_rep.set_defaults(func=cmd_reproduce)

    # Subcommand: run-all
    p_all = subparsers.add_parser("run-all", help="Execute complete end-to-end pipeline")
    p_all.add_argument("--seed", type=int, default=DEFAULT_RANDOM_SEED, help="Random seed")
    p_all.add_argument("--profile", type=str, default="starter", choices=["starter", "medium", "full"], help="Scale profile")
    p_all.add_argument("--export-dir", type=str, default="exports", help="Target export directory")
    p_all.add_argument("--data-dir", type=str, default="exports", help="Data directory for validation/forecasting")
    p_all.add_argument("--holdout-days", type=int, default=14, help="Holdout evaluation window days")
    p_all.add_argument("--export-file", type=str, default=None, help="Output JSON path")
    p_all.add_argument("--inject-anomalies", action="store_true", default=True, help="Inject 5 labelled edge cases")
    p_all.set_defaults(func=cmd_run_all)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

