"""SQL DDL Generator for Relational Database Persistence.

Generates ANSI SQL / PostgreSQL compatible CREATE TABLE statements,
foreign key constraints, and performance indexes for all replenishment engine entities.
"""

from typing import Dict
from replenishment_engine.schemas.data_dictionary import DATA_DICTIONARY


TYPE_MAP = {
    "string": "VARCHAR(255)",
    "integer": "INTEGER",
    "float": "NUMERIC(14, 4)",
    "date": "DATE",
    "boolean": "BOOLEAN",
}


def generate_sql_ddl() -> str:
    """Generates complete SQL DDL schema with primary keys, foreign keys, and indexes."""
    statements = [
        "-- ============================================================================",
        "-- SKU-Location Demand Forecasting & Replenishment Engine DDL Schema",
        "-- Auto-generated from Data Dictionary Specifications",
        "-- ============================================================================\n",
    ]

    # Generate CREATE TABLE statements
    for entity_name, entity in DATA_DICTIONARY.items():
        tbl = entity.table_name
        statements.append(f"DROP TABLE IF EXISTS {tbl} CASCADE;")
        statements.append(f"CREATE TABLE {tbl} (")
        col_defs = []
        pks = []
        fks = []

        for f in entity.fields:
            sql_type = TYPE_MAP.get(f.data_type, "VARCHAR(255)")
            null_clause = "NOT NULL" if f.required else "NULL"
            col_defs.append(f"    {f.name} {sql_type} {null_clause}")
            if f.is_primary_key:
                pks.append(f.name)
            if f.foreign_key:
                ref_parts = f.foreign_key.split(".")
                ref_entity = ref_parts[0]
                ref_field = ref_parts[1]
                ref_tbl = DATA_DICTIONARY[ref_entity].table_name
                fks.append(f"    CONSTRAINT fk_{tbl}_{f.name} FOREIGN KEY ({f.name}) REFERENCES {ref_tbl}({ref_field})")

        if pks:
            col_defs.append(f"    CONSTRAINT pk_{tbl} PRIMARY KEY ({', '.join(pks)})")
        col_defs.extend(fks)

        statements.append(",\n".join(col_defs))
        statements.append(");\n")

        # Create indexes on foreign keys
        for f in entity.fields:
            if f.foreign_key:
                statements.append(f"CREATE INDEX idx_{tbl}_{f.name} ON {tbl}({f.name});")
        statements.append("")

    return "\n".join(statements)

