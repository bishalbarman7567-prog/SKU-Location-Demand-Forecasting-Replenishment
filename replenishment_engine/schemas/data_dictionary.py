"""Data Dictionary and Entity Schema Specifications.

Defines schemas, types, nullability, allowed values, units, uniqueness,
and validation rules for all 10 core entities plus event log and ground truth.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import json


@dataclass
class FieldDefinition:
    """Definition of a single field in an entity."""
    name: str
    data_type: str
    required: bool
    allowed_values: Optional[str]
    units: Optional[str]
    is_primary_key: bool
    foreign_key: Optional[str]
    validation_rule: str
    description: str


@dataclass
class EntityDefinition:
    """Definition of an entity / table in the schema."""
    entity_name: str
    table_name: str
    cardinality_notes: str
    lifecycle_states: Optional[List[str]]
    fields: List[FieldDefinition] = field(default_factory=list)


DATA_DICTIONARY: Dict[str, EntityDefinition] = {
    "SKU": EntityDefinition(
        entity_name="SKU",
        table_name="skus",
        cardinality_notes="1:N with SalesHistory, InventorySnapshot, SupplierSKU, Forecast, ReorderPolicy, PurchaseRecommendation",
        lifecycle_states=["ACTIVE", "PHASE_OUT", "DISCONTINUED"],
        fields=[
            FieldDefinition("sku_id", "string", True, "Regex: SKU-[0-9]{6}", "ID", True, None, "Must match SKU-XXXXXX and be unique", "Primary key for Stock Keeping Unit"),
            FieldDefinition("sku_name", "string", True, "Any non-empty string", "Text", False, None, "Length between 3 and 100 characters", "Human-readable merchandise title"),
            FieldDefinition("category", "string", True, "Beverages, Dairy, Bakery, Pantry, Produce, Frozen, Personal Care, Household", "Category", False, None, "Must be valid department enum", "Product merchandise category"),
            FieldDefinition("unit_cost", "float", True, ">= 0.01", "USD ($)", False, None, "Positive decimal, unit_cost < unit_price", "Standard baseline unit procurement cost"),
            FieldDefinition("unit_price", "float", True, ">= 0.02", "USD ($)", False, None, "Positive decimal, unit_price > unit_cost", "Retail shelf/listing price"),
            FieldDefinition("unit_volume_m3", "float", True, ">= 0.0001", "Cubic Meters (m3)", False, None, "Positive decimal", "Physical storage volume per unit"),
            FieldDefinition("unit_weight_kg", "float", True, ">= 0.01", "Kilograms (kg)", False, None, "Positive decimal", "Physical weight per unit"),
            FieldDefinition("status", "string", True, "ACTIVE, PHASE_OUT, DISCONTINUED", "Enum", False, None, "Must match valid lifecycle enum", "Current product lifecycle phase"),
            FieldDefinition("launch_date", "date", True, "YYYY-MM-DD", "Date", False, None, "Valid ISO date <= discontinue_date", "Date product introduced to inventory"),
            FieldDefinition("discontinue_date", "date", False, "YYYY-MM-DD or NULL", "Date", False, None, "ISO date > launch_date if present", "Date product was retired if discontinued"),
        ]
    ),
    "Store": EntityDefinition(
        entity_name="Store",
        table_name="stores",
        cardinality_notes="1:N with SalesHistory, InventorySnapshot, Forecast, ReorderPolicy, PurchaseRecommendation",
        lifecycle_states=["ACTIVE", "RENOVATING", "CLOSED"],
        fields=[
            FieldDefinition("store_id", "string", True, "Regex: STORE-[0-9]{6}", "ID", True, None, "Must match STORE-XXXXXX and be unique", "Primary key for retail store/facility"),
            FieldDefinition("store_name", "string", True, "Any non-empty string", "Text", False, None, "Length between 3 and 100 characters", "Facility name/location"),
            FieldDefinition("channel", "string", True, "RETAIL_SUPERMARKET, CONVENIENCE, ECOMM_HUB, REGIONAL_DC", "Enum", False, None, "Must match channel enum", "Fulfillment channel and operating model"),
            FieldDefinition("region", "string", True, "North, South, East, West, Central", "Enum", False, None, "Must match region enum", "Geographic operating market"),
            FieldDefinition("max_storage_units", "integer", True, "1000 - 1000000", "Units", False, None, "Positive integer >= 1000", "Maximum unit capacity threshold of store backroom/shelves"),
            FieldDefinition("max_storage_volume_m3", "float", True, ">= 50.0", "Cubic Meters (m3)", False, None, "Positive float", "Maximum physical backroom volume capacity"),
            FieldDefinition("replenishment_cadence_days", "integer", True, "1, 2, 7", "Days", False, None, "In [1, 2, 7]", "Review interval frequency for ordering"),
            FieldDefinition("opened_date", "date", True, "YYYY-MM-DD", "Date", False, None, "Valid ISO date", "Date facility opened for operations"),
        ]
    ),
    "Supplier": EntityDefinition(
        entity_name="Supplier",
        table_name="suppliers",
        cardinality_notes="1:N with SupplierSKU, LeadTimeObservation, PurchaseRecommendation",
        lifecycle_states=["ACTIVE", "ON_PROBATION", "SUSPENDED"],
        fields=[
            FieldDefinition("supplier_id", "string", True, "Regex: SUPP-[0-9]{4}", "ID", True, None, "Must match SUPP-XXXX and be unique", "Primary key for external vendor"),
            FieldDefinition("supplier_name", "string", True, "Any non-empty string", "Text", False, None, "Length between 3 and 100 characters", "Legal commercial vendor name"),
            FieldDefinition("tier", "string", True, "TIER_1, TIER_2, TIER_3", "Enum", False, None, "Must match tier enum", "Strategic vendor classification tier"),
            FieldDefinition("reliability_score", "float", True, "0.50 - 1.00", "Score", False, None, "0.0 <= score <= 1.0", "Historical On-Time In-Full fulfillment index"),
            FieldDefinition("payment_terms_days", "integer", True, "15, 30, 45, 60, 90", "Days", False, None, "Positive integer", "Standard commercial credit terms"),
            FieldDefinition("country", "string", True, "ISO-3166-1 alpha-2 or standard name", "Country", False, None, "Valid 2-letter country code", "Supplier headquarters country"),
        ]
    ),
    "SupplierSKU": EntityDefinition(
        entity_name="SupplierSKU",
        table_name="supplier_skus",
        cardinality_notes="N:M Bridge table between Supplier (1:N) and SKU (1:N). 1:N with LeadTimeObservation",
        lifecycle_states=["ACTIVE", "INACTIVE"],
        fields=[
            FieldDefinition("supplier_sku_id", "string", True, "Regex: SSKU-SUPP-[0-9]{4}-SKU-[0-9]{6}", "ID", True, None, "Unique compound bridge ID", "Primary key for vendor-SKU contract relation"),
            FieldDefinition("supplier_id", "string", True, "Regex: SUPP-[0-9]{4}", "ID", False, "Supplier.supplier_id", "Must reference existing Supplier", "Foreign key to vendor entity"),
            FieldDefinition("sku_id", "string", True, "Regex: SKU-[0-9]{6}", "ID", False, "SKU.sku_id", "Must reference existing SKU", "Foreign key to SKU entity"),
            FieldDefinition("pack_size", "integer", True, "1, 6, 12, 24, 48, 96", "Units/Pack", False, None, "Positive integer >= 1", "Master carton case pack multiple"),
            FieldDefinition("moq_units", "integer", True, ">= pack_size", "Units", False, None, "Must be positive integer and multiple of pack_size", "Minimum order quantity in units"),
            FieldDefinition("unit_purchase_cost", "float", True, ">= 0.01", "USD ($)", False, None, "Must be positive decimal", "Negotiated contract unit procurement cost"),
            FieldDefinition("nominal_lead_time_days", "integer", True, "1 - 60", "Days", False, None, "Positive integer >= 1", "Expected supplier order fulfillment duration"),
            FieldDefinition("lead_time_std_days", "float", True, "0.1 - 10.0", "Days", False, None, "Non-negative float", "Standard deviation of delivery lead times"),
            FieldDefinition("is_primary", "boolean", True, "True, False", "Boolean", False, None, "Exactly one primary supplier per SKU", "Indicator for primary source of supply"),
            FieldDefinition("effective_from", "date", True, "YYYY-MM-DD", "Date", False, None, "Valid ISO date", "Contract start validity date"),
            FieldDefinition("effective_to", "date", False, "YYYY-MM-DD or NULL", "Date", False, None, "ISO date >= effective_from if present", "Contract expiration validity date"),
        ]
    ),
    "SalesHistory": EntityDefinition(
        entity_name="SalesHistory",
        table_name="sales_history",
        cardinality_notes="N:1 with Store, N:1 with SKU. Daily transactions / demand log",
        lifecycle_states=None,
        fields=[
            FieldDefinition("sale_id", "string", True, "SALE-<store-id>-<sku-id>-<date>", "ID", True, None, "Unique composite key format SALE-STORE-XXXXXX-SKU-XXXXXX-YYYY-MM-DD", "Primary transaction record key"),
            FieldDefinition("store_id", "string", True, "Regex: STORE-[0-9]{6}", "ID", False, "Store.store_id", "Must exist in Store", "Foreign key to Store"),
            FieldDefinition("sku_id", "string", True, "Regex: SKU-[0-9]{6}", "ID", False, "SKU.sku_id", "Must exist in SKU", "Foreign key to SKU"),
            FieldDefinition("date", "date", True, "YYYY-MM-DD", "Date", False, None, "Valid ISO date within observation window", "Transaction calendar date"),
            FieldDefinition("units_sold", "integer", True, ">= 0", "Units", False, None, "Integer >= 0. Must be 0 if stockout occurred at day start", "Actual recorded physical sales transactions"),
            FieldDefinition("promotion_flag", "boolean", True, "True, False", "Boolean", False, None, "Boolean indicator", "Whether promotional event/flyer was active"),
            FieldDefinition("promo_discount_pct", "float", True, "0.00 - 0.50", "Percentage", False, None, "0.0 if promotion_flag is False, > 0 if True", "Promotional price discount fraction"),
            FieldDefinition("stockout_flag", "boolean", True, "True, False", "Boolean", False, None, "Boolean indicator", "True if zero on-hand prevented full demand fulfillment"),
            FieldDefinition("unconstrained_demand_est", "float", True, ">= units_sold", "Units", False, None, "Must be >= units_sold", "True unconstrained demand before inventory censoring"),
            FieldDefinition("lost_sales_units", "float", True, ">= 0.0", "Units", False, None, "Equals unconstrained_demand_est - units_sold", "Sales lost due to stockout censoring"),
            FieldDefinition("unit_selling_price", "float", True, ">= 0.01", "USD ($)", False, None, "Positive float", "Actual price charged per unit after discount"),
            FieldDefinition("gross_revenue", "float", True, ">= 0.0", "USD ($)", False, None, "Equals units_sold * unit_selling_price", "Total gross transaction sales revenue"),
        ]
    ),
    "InventorySnapshot": EntityDefinition(
        entity_name="InventorySnapshot",
        table_name="inventory_snapshots",
        cardinality_notes="N:1 with Store, N:1 with SKU. Daily end-of-day stock positions",
        lifecycle_states=None,
        fields=[
            FieldDefinition("snapshot_id", "string", True, "INV-<store-id>-<sku-id>-<date>", "ID", True, None, "Unique composite key format INV-STORE-XXXXXX-SKU-XXXXXX-YYYY-MM-DD", "Primary daily snapshot record key"),
            FieldDefinition("store_id", "string", True, "Regex: STORE-[0-9]{6}", "ID", False, "Store.store_id", "Must exist in Store", "Foreign key to Store"),
            FieldDefinition("sku_id", "string", True, "Regex: SKU-[0-9]{6}", "ID", False, "SKU.sku_id", "Must exist in SKU", "Foreign key to SKU"),
            FieldDefinition("date", "date", True, "YYYY-MM-DD", "Date", False, None, "Valid ISO date", "Snapshot calendar date"),
            FieldDefinition("opening_on_hand_qty", "integer", True, ">= 0", "Units", False, None, "Non-negative integer", "Stock on shelf/backroom at day start"),
            FieldDefinition("received_qty", "integer", True, ">= 0", "Units", False, None, "Non-negative integer", "Stock delivered from POs during day"),
            FieldDefinition("units_sold", "integer", True, ">= 0", "Units", False, None, "Must match SalesHistory.units_sold", "Stock depleted through sales"),
            FieldDefinition("closing_on_hand_qty", "integer", True, ">= 0", "Units", False, None, "Equals opening + received - units_sold", "End of day physical stock on hand"),
            FieldDefinition("on_order_qty", "integer", True, ">= 0", "Units", False, None, "Non-negative integer", "Stock in transit or committed on open purchase orders"),
            FieldDefinition("reserved_qty", "integer", True, ">= 0", "Units", False, None, "Non-negative integer <= closing_on_hand_qty", "Stock allocated to pending customer click-and-collect"),
            FieldDefinition("available_qty", "integer", True, ">= 0", "Units", False, None, "Equals closing_on_hand + on_order - reserved", "Effective net available stock position"),
            FieldDefinition("stockout_flag", "boolean", True, "True, False", "Boolean", False, None, "True if closing_on_hand_qty == 0", "Binary indicator of zero stockout state"),
            FieldDefinition("days_of_supply", "float", True, ">= 0.0", "Days", False, None, "available_qty / max(daily_demand, 0.01)", "Runway of stock based on average daily velocity"),
        ]
    ),
    "LeadTimeObservation": EntityDefinition(
        entity_name="LeadTimeObservation",
        table_name="lead_time_observations",
        cardinality_notes="N:1 with Supplier, N:1 with SKU, N:1 with SupplierSKU. Historical PO lead-time receipts",
        lifecycle_states=["ON_TIME", "DELAYED", "EARLY", "CANCELLED"],
        fields=[
            FieldDefinition("observation_id", "string", True, "Regex: LTO-[0-9]{6}", "ID", True, None, "Unique zero-padded sequential ID", "Primary key for lead time fulfillment event"),
            FieldDefinition("po_id", "string", True, "Regex: PO-[0-9]{4}-[0-9]{6}", "ID", False, "PurchaseRecommendation.recommendation_id", "References originating purchase order", "Foreign key to purchase order"),
            FieldDefinition("supplier_id", "string", True, "Regex: SUPP-[0-9]{4}", "ID", False, "Supplier.supplier_id", "Must exist in Supplier", "Foreign key to vendor"),
            FieldDefinition("sku_id", "string", True, "Regex: SKU-[0-9]{6}", "ID", False, "SKU.sku_id", "Must exist in SKU", "Foreign key to SKU"),
            FieldDefinition("order_date", "date", True, "YYYY-MM-DD", "Date", False, None, "Valid ISO date", "Date PO was dispatched to vendor"),
            FieldDefinition("expected_delivery_date", "date", True, "YYYY-MM-DD", "Date", False, None, "Must be >= order_date", "Promised contract delivery arrival date"),
            FieldDefinition("actual_delivery_date", "date", True, "YYYY-MM-DD", "Date", False, None, "Must be >= order_date (unless flagged anomalous)", "Actual dock receipt date"),
            FieldDefinition("nominal_lead_time_days", "integer", True, ">= 1", "Days", False, None, "Positive integer", "Contracted nominal lead time"),
            FieldDefinition("actual_lead_time_days", "integer", True, "Any integer", "Days", False, None, "actual_delivery_date - order_date; >= 0 for valid rows", "Empirical fulfillment days elapsed"),
            FieldDefinition("lead_time_variance_days", "integer", True, "Any integer", "Days", False, None, "actual_lead_time_days - nominal_lead_time_days", "Lateness vs nominal expectation"),
            FieldDefinition("status", "string", True, "ON_TIME, DELAYED, EARLY, CANCELLED", "Enum", False, None, "Must match fulfillment status enum", "Receipt punctuality classification"),
            FieldDefinition("delay_reason", "string", False, "PORT_CONGESTION, FACTORY_DELAY, CARRIER_BREAKDOWN, WEATHER, NONE", "Text", False, None, "Optional text explanation", "Root cause of fulfillment variance"),
        ]
    ),
    "Forecast": EntityDefinition(
        entity_name="Forecast",
        table_name="forecasts",
        cardinality_notes="N:1 with Store, N:1 with SKU. Statistical demand projections per SKU-store",
        lifecycle_states=None,
        fields=[
            FieldDefinition("forecast_id", "string", True, "Regex: FC-<store-id>-<sku-id>-<date>", "ID", True, None, "Unique composite key format FC-STORE-XXXXXX-SKU-XXXXXX-YYYY-MM-DD", "Primary demand forecast projection key"),
            FieldDefinition("store_id", "string", True, "Regex: STORE-[0-9]{6}", "ID", False, "Store.store_id", "Must exist in Store", "Foreign key to Store"),
            FieldDefinition("sku_id", "string", True, "Regex: SKU-[0-9]{6}", "ID", False, "SKU.sku_id", "Must exist in SKU", "Foreign key to SKU"),
            FieldDefinition("forecast_date", "date", True, "YYYY-MM-DD", "Date", False, None, "Valid ISO date as-of forecast run", "Date prediction was generated"),
            FieldDefinition("horizon_start_date", "date", True, "YYYY-MM-DD", "Date", False, None, "Must be >= forecast_date", "First day of prediction interval"),
            FieldDefinition("horizon_end_date", "date", True, "YYYY-MM-DD", "Date", False, None, "Must be > horizon_start_date", "Last day of prediction interval"),
            FieldDefinition("horizon_days", "integer", True, "7, 14, 30", "Days", False, None, "Positive integer", "Forecast lookahead horizon duration"),
            FieldDefinition("forecasted_daily_demand", "float", True, ">= 0.0", "Units/Day", False, None, "Non-negative float", "Estimated mean daily unit velocity"),
            FieldDefinition("forecasted_daily_std", "float", True, ">= 0.0", "Units/Day", False, None, "Non-negative float", "Estimated standard deviation of daily demand"),
            FieldDefinition("forecasted_total_horizon_demand", "float", True, ">= 0.0", "Units", False, None, "Equals forecasted_daily_demand * horizon_days", "Integrated demand over entire horizon"),
            FieldDefinition("method", "string", True, "HOLT_WINTERS, CROSTON_INTERMITTENT, EXPONENTIAL_SMOOTHING, UNCENSORED_MOVING_AVERAGE", "Enum", False, None, "Must match forecasting model enum", "Statistical model used to generate estimate"),
            FieldDefinition("promo_uplift_factor", "float", True, ">= 1.0", "Multiplier", False, None, "Float >= 1.0", "Anticipated lift factor for planned promotions"),
            FieldDefinition("stockout_uncensored", "boolean", True, "True, False", "Boolean", False, None, "Boolean indicator", "Whether lost sales imputation was applied to training data"),
            FieldDefinition("created_at", "string", True, "ISO-8601 Timestamp", "Timestamp", False, None, "Valid ISO-8601 timestamp", "System timestamp when forecast was written"),
        ]
    ),
    "ReorderPolicy": EntityDefinition(
        entity_name="ReorderPolicy",
        table_name="reorder_policies",
        cardinality_notes="1:1 per SKU-Store active horizon. Governs replenishment triggers",
        lifecycle_states=["ACTIVE", "REVISED", "DEPRECATED"],
        fields=[
            FieldDefinition("policy_id", "string", True, "Regex: RP-<store-id>-<sku-id>", "ID", True, None, "Unique compound key format RP-STORE-XXXXXX-SKU-XXXXXX", "Primary reorder parameterization key"),
            FieldDefinition("store_id", "string", True, "Regex: STORE-[0-9]{6}", "ID", False, "Store.store_id", "Must exist in Store", "Foreign key to Store"),
            FieldDefinition("sku_id", "string", True, "Regex: SKU-[0-9]{6}", "ID", False, "SKU.sku_id", "Must exist in SKU", "Foreign key to SKU"),
            FieldDefinition("service_level", "float", True, "0.85 - 0.999", "Ratio", False, None, "Float between 0.80 and 0.999", "Target cycle service level probability (1 - Stockout Risk)"),
            FieldDefinition("z_factor", "float", True, "1.28 - 3.09", "Standard Score", False, None, "Inverse standard normal CDF of service_level", "Safety stock statistical multiplier"),
            FieldDefinition("effective_lead_time_days", "float", True, ">= 1.0", "Days", False, None, "Positive float", "Mean supplier replenishment lead time"),
            FieldDefinition("lead_time_demand", "float", True, ">= 0.0", "Units", False, None, "Equals daily_demand * lead_time", "Expected mean sales during fulfillment window"),
            FieldDefinition("safety_stock_units", "integer", True, ">= 0", "Units", False, None, "Z * sqrt(L * std_d^2 + d^2 * std_L^2)", "Buffer stock protecting against demand & lead time variance"),
            FieldDefinition("reorder_point_units", "integer", True, ">= safety_stock_units", "Units", False, None, "Equals lead_time_demand + safety_stock_units", "Inventory position threshold triggering replenishment order"),
            FieldDefinition("target_stock_level", "integer", True, ">= reorder_point_units", "Units", False, None, "Equals ROP + (ReviewPeriod * daily_demand)", "Order-up-to stock target ceiling"),
            FieldDefinition("review_period_days", "integer", True, "1 - 14", "Days", False, None, "Positive integer", "Frequency of replenishment review in days"),
            FieldDefinition("max_store_capacity_units", "integer", True, ">= 10", "Units", False, None, "Positive integer", "Hard shelf/backroom allocation ceiling for this SKU-store"),
            FieldDefinition("last_updated", "date", True, "YYYY-MM-DD", "Date", False, None, "Valid ISO date", "Date policy parameters were recalculated"),
        ]
    ),
    "PurchaseRecommendation": EntityDefinition(
        entity_name="PurchaseRecommendation",
        table_name="purchase_recommendations",
        cardinality_notes="N:1 with Store, N:1 with SKU, N:1 with Supplier. 1:N with OrderLifecycleEvent",
        lifecycle_states=["RECOMMENDED", "APPROVED", "REJECTED", "EXCEPTION_FLAGGED", "ORDERED"],
        fields=[
            FieldDefinition("recommendation_id", "string", True, "Regex: PO-[0-9]{4}-[0-9]{6}", "ID", True, None, "Unique sequential key format PO-YYYY-XXXXXX", "Primary replenishment recommendation key"),
            FieldDefinition("store_id", "string", True, "Regex: STORE-[0-9]{6}", "ID", False, "Store.store_id", "Must exist in Store", "Foreign key to destination facility"),
            FieldDefinition("sku_id", "string", True, "Regex: SKU-[0-9]{6}", "ID", False, "SKU.sku_id", "Must exist in SKU", "Foreign key to replenishing item"),
            FieldDefinition("supplier_id", "string", True, "Regex: SUPP-[0-9]{4}", "ID", False, "Supplier.supplier_id", "Must exist in Supplier", "Foreign key to vendor providing goods"),
            FieldDefinition("recommendation_date", "date", True, "YYYY-MM-DD", "Date", False, None, "Valid ISO date", "Date recommendation was generated by engine"),
            FieldDefinition("current_on_hand_qty", "integer", True, ">= 0", "Units", False, None, "Current physical stock", "On-hand inventory at recommendation time"),
            FieldDefinition("current_on_order_qty", "integer", True, ">= 0", "Units", False, None, "Open pipeline stock", "Inventory already on order with supplier"),
            FieldDefinition("current_reserved_qty", "integer", True, ">= 0", "Units", False, None, "Committed orders", "Inventory committed to pending fulfillments"),
            FieldDefinition("net_inventory_position", "integer", True, "Any integer", "Units", False, None, "on_hand + on_order - reserved", "Effective net stock position"),
            FieldDefinition("reorder_point", "integer", True, ">= 0", "Units", False, None, "From ReorderPolicy", "Trigger threshold for ordering"),
            FieldDefinition("target_stock_level", "integer", True, ">= reorder_point", "Units", False, None, "From ReorderPolicy", "Target order-up-to level"),
            FieldDefinition("gross_need_units", "integer", True, ">= 0", "Units", False, None, "max(0, target_stock_level - net_inventory_position)", "Deficit needed to reach target stock level"),
            FieldDefinition("unrounded_order_qty", "integer", True, ">= 0", "Units", False, None, "max(gross_need, MOQ) if gross_need > 0 else 0", "Required order quantity before pack-size rounding"),
            FieldDefinition("pack_size_applied", "integer", True, ">= 1", "Units/Pack", False, None, "Contract supplier pack size", "Pack size multiple applied for rounding"),
            FieldDefinition("moq_applied", "integer", True, ">= 0", "Units", False, None, "Contract minimum order quantity", "Vendor MOQ applied"),
            FieldDefinition("capacity_constrained_qty", "integer", True, ">= 0", "Units", False, None, "Order quantity respecting store storage limits", "Quantity capped by store backroom/shelf capacity"),
            FieldDefinition("final_order_qty", "integer", True, ">= 0", "Units", False, None, "Must be multiple of pack_size and >= MOQ if ordered, unless exception", "Recommended final unit order quantity"),
            FieldDefinition("unit_cost", "float", True, ">= 0.01", "USD ($)", False, None, "Procurement unit contract cost", "Purchase cost per unit"),
            FieldDefinition("total_cost", "float", True, ">= 0.0", "USD ($)", False, None, "final_order_qty * unit_cost", "Total financial commitment for this purchase recommendation"),
            FieldDefinition("priority", "string", True, "CRITICAL_STOCKOUT, HIGH_RISK, ROUTINE, SEASONAL_BUILD", "Enum", False, None, "Must match priority enum", "Urgency level for operational review"),
            FieldDefinition("status", "string", True, "RECOMMENDED, APPROVED, REJECTED, EXCEPTION_FLAGGED, ORDERED", "Enum", False, None, "Must match recommendation status enum", "Current state in approval lifecycle"),
            FieldDefinition("exception_code", "string", True, "NONE, ERR_DISCONTINUED_SKU, ERR_CAPACITY_EXCEEDED, ERR_PACK_SIZE_MISMATCH, ERR_NEGATIVE_LEAD_TIME, ERR_SUPPLIER_INACTIVE", "Enum", False, None, "Must match exception enum", "Audit error code if rule condition violated"),
            FieldDefinition("rationale", "string", True, "Any explanatory text", "Text", False, None, "Detailed transparent explanation", "Plain language operational justification and math trace"),
            FieldDefinition("created_at", "string", True, "ISO-8601 Timestamp", "Timestamp", False, None, "Valid ISO-8601 timestamp", "Record creation timestamp"),
        ]
    ),
    "OrderLifecycleEvent": EntityDefinition(
        entity_name="OrderLifecycleEvent",
        table_name="order_lifecycle_events",
        cardinality_notes="N:1 with PurchaseRecommendation. Audit trail preserving state transitions",
        lifecycle_states=None,
        fields=[
            FieldDefinition("event_id", "string", True, "Regex: EVT-[0-9]{6}", "ID", True, None, "Unique sequential key format EVT-XXXXXX", "Primary key for event audit record"),
            FieldDefinition("recommendation_id", "string", True, "Regex: PO-[0-9]{4}-[0-9]{6}", "ID", False, "PurchaseRecommendation.recommendation_id", "Must exist in PurchaseRecommendation", "Foreign key to recommendation"),
            FieldDefinition("from_status", "string", True, "Any status or NONE", "Enum", False, None, "Prior state in lifecycle", "Previous recommendation state"),
            FieldDefinition("to_status", "string", True, "RECOMMENDED, APPROVED, REJECTED, EXCEPTION_FLAGGED, ORDERED", "Enum", False, None, "Valid recommendation lifecycle state", "New recommendation state"),
            FieldDefinition("actor", "string", True, "System/ReplenishmentEngine, StoreManager, MerchandisingAnalyst, OperationsManager", "Role", False, None, "Authorized user or system role", "Actor who triggered the state change"),
            FieldDefinition("action", "string", True, "GENERATE, APPROVE, OVERRIDE_QTY, REJECT, DISPATCH, ESCALATE", "Action", False, None, "Business action verb", "Action performed on recommendation"),
            FieldDefinition("notes", "string", True, "Audit text log", "Text", False, None, "Audit comments or system decision reasoning", "Explanatory remarks accompanying state transition"),
            FieldDefinition("timestamp", "string", True, "ISO-8601 Timestamp", "Timestamp", False, None, "Valid ISO-8601 timestamp", "Wall clock timestamp of event occurrence"),
        ]
    ),
}


def export_data_dictionary_markdown() -> str:
    """Renders the data dictionary into GitHub-flavored Markdown tables."""
    md_lines = ["# SKU-Location Demand Forecasting & Replenishment Data Dictionary\n"]
    for entity_name, entity in DATA_DICTIONARY.items():
        md_lines.append(f"## Entity: `{entity.entity_name}` (Table: `{entity.table_name}`)")
        md_lines.append(f"**Cardinality & Relationships:** {entity.cardinality_notes}")
        if entity.lifecycle_states:
            md_lines.append(f"**Lifecycle States:** `{', '.join(entity.lifecycle_states)}`")
        md_lines.append("\n| Field Name | Type | Req | Allowed Values | Units | PK | FK Reference | Validation Rule | Description |")
        md_lines.append("|---|---|---|---|---|---|---|---|---|")
        for f in entity.fields:
            fk_str = f.foreign_key if f.foreign_key else "-"
            units_str = f.units if f.units else "-"
            md_lines.append(
                f"| `{f.name}` | {f.data_type} | {'Yes' if f.required else 'No'} | "
                f"{f.allowed_values} | {units_str} | {'PK' if f.is_primary_key else '-'} | "
                f"{fk_str} | {f.validation_rule} | {f.description} |"
            )
        md_lines.append("\n---\n")
    return "\n".join(md_lines)


def export_data_dictionary_json() -> str:
    """Exports data dictionary metadata as structured JSON."""
    dict_payload = {}
    for entity_name, entity in DATA_DICTIONARY.items():
        dict_payload[entity_name] = {
            "entity_name": entity.entity_name,
            "table_name": entity.table_name,
            "cardinality_notes": entity.cardinality_notes,
            "lifecycle_states": entity.lifecycle_states,
            "fields": [f.__dict__ for f in entity.fields],
        }
    return json.dumps(dict_payload, indent=2)

