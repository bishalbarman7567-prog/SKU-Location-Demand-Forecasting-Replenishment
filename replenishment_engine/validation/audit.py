"""Audit, Hashing and Step 10 Reproducibility Verification Module.

Computes SHA-256 checksums, compiles dataset manifests, and verifies bit-for-bit
reproducibility across independent generator executions using the same random seed.
"""

import hashlib
import json
from datetime import datetime
from typing import Dict, Any, Tuple
import pandas as pd

from replenishment_engine.generator.synthetic_data_generator import ReplenishmentDataGenerator
from replenishment_engine.config import DEFAULT_RANDOM_SEED


def compute_dataframe_checksum(df: pd.DataFrame) -> str:
    """Computes a deterministic SHA-256 hex digest of a DataFrame's CSV representation."""
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    return hashlib.sha256(csv_bytes).hexdigest()


def generate_manifest(tables: Dict[str, pd.DataFrame], seed: int, profile: str) -> Dict[str, Any]:
    """Compiles source manifest containing metadata, schema details, row counts and checksums."""
    manifest = {
        "manifest_version": "1.0.0",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "random_seed": seed,
        "scale_profile": profile,
        "total_entities": len(tables),
        "total_records": sum(len(df) for df in tables.values()),
        "tables": {},
    }

    for name, df in tables.items():
        manifest["tables"][name] = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
            "sha256_checksum": compute_dataframe_checksum(df),
            "memory_usage_bytes": int(df.memory_usage(deep=True).sum()),
        }

    return manifest


def verify_reproducibility(seed: int = DEFAULT_RANDOM_SEED, profile: str = "starter") -> Dict[str, Any]:
    """Step 10 Acceptance Test: Regenerates twice with identical seed and proves bit-for-bit matching."""
    gen_run_1 = ReplenishmentDataGenerator(seed=seed, profile_name=profile)
    tables_run_1 = gen_run_1.generate_all()

    gen_run_2 = ReplenishmentDataGenerator(seed=seed, profile_name=profile)
    tables_run_2 = gen_run_2.generate_all()

    table_comparisons = {}
    all_matched = True

    for name in tables_run_1.keys():
        df1 = tables_run_1[name]
        df2 = tables_run_2[name]

        rows_match = len(df1) == len(df2)
        hash1 = compute_dataframe_checksum(df1)
        hash2 = compute_dataframe_checksum(df2)
        hashes_match = hash1 == hash2

        matched = rows_match and hashes_match
        if not matched:
            all_matched = False

        table_comparisons[name] = {
            "run_1_rows": len(df1),
            "run_2_rows": len(df2),
            "run_1_sha256": hash1,
            "run_2_sha256": hash2,
            "row_counts_match": rows_match,
            "checksums_match": hashes_match,
            "bit_for_bit_identical": matched,
        }

    return {
        "is_reproducible": all_matched,
        "tested_seed": seed,
        "tested_profile": profile,
        "tables_evaluated": len(table_comparisons),
        "table_details": table_comparisons,
    }

