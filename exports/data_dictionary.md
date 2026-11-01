# SKU-Location Demand Forecasting & Replenishment Data Dictionary

## Entity: `SKU` (Table: `skus`)
**Cardinality & Relationships:** 1:N with SalesHistory, InventorySnapshot, SupplierSKU, Forecast, ReorderPolicy, PurchaseRecommendation
**Lifecycle States:** `ACTIVE, PHASE_OUT, DISCONTINUED`

| Field Name | Type | Req | Allowed Values | Units | PK | FK Reference | Validation Rule | Description |
|---|---|---|---|---|---|---|---|---|
| `sku_id` | string | Yes | Regex: SKU-[0-9]{6} | ID | PK | - | Must match SKU-XXXXXX and be unique | Primary key for Stock Keeping Unit |
| `sku_name` | string | Yes | Any non-empty string | Text | - | - | Length between 3 and 100 characters | Human-readable merchandise title |
| `category` | string | Yes | Beverages, Dairy, Bakery, Pantry, Produce, Frozen, Personal Care, Household | Category | - | - | Must be valid department enum | Product merchandise category |
| `unit_cost` | float | Yes | >= 0.01 | USD ($) | - | - | Positive decimal, unit_cost < unit_price | Standard baseline unit procurement cost |
| `unit_price` | float | Yes | >= 0.02 | USD ($) | - | - | Positive decimal, unit_price > unit_cost | Retail shelf/listing price |
| `unit_volume_m3` | float | Yes | >= 0.0001 | Cubic Meters (m3) | - | - | Positive decimal | Physical storage volume per unit |
| `unit_weight_kg` | float | Yes | >= 0.01 | Kilograms (kg) | - | - | Positive decimal | Physical weight per unit |
| `status` | string | Yes | ACTIVE, PHASE_OUT, DISCONTINUED | Enum | - | - | Must match valid lifecycle enum | Current product lifecycle phase |
| `launch_date` | date | Yes | YYYY-MM-DD | Date | - | - | Valid ISO date <= discontinue_date | Date product introduced to inventory |
| `discontinue_date` | date | No | YYYY-MM-DD or NULL | Date | - | - | ISO date > launch_date if present | Date product was retired if discontinued |

---

## Entity: `Store` (Table: `stores`)
**Cardinality & Relationships:** 1:N with SalesHistory, InventorySnapshot, Forecast, ReorderPolicy, PurchaseRecommendation
**Lifecycle States:** `ACTIVE, RENOVATING, CLOSED`

| Field Name | Type | Req | Allowed Values | Units | PK | FK Reference | Validation Rule | Description |
|---|---|---|---|---|---|---|---|---|
| `store_id` | string | Yes | Regex: STORE-[0-9]{6} | ID | PK | - | Must match STORE-XXXXXX and be unique | Primary key for retail store/facility |
| `store_name` | string | Yes | Any non-empty string | Text | - | - | Length between 3 and 100 characters | Facility name/location |
| `channel` | string | Yes | RETAIL_SUPERMARKET, CONVENIENCE, ECOMM_HUB, REGIONAL_DC | Enum | - | - | Must match channel enum | Fulfillment channel and operating model |
| `region` | string | Yes | North, South, East, West, Central | Enum | - | - | Must match region enum | Geographic operating market |
| `max_storage_units` | integer | Yes | 1000 - 1000000 | Units | - | - | Positive integer >= 1000 | Maximum unit capacity threshold of store backroom/shelves |
| `max_storage_volume_m3` | float | Yes | >= 50.0 | Cubic Meters (m3) | - | - | Positive float | Maximum physical backroom volume capacity |
| `replenishment_cadence_days` | integer | Yes | 1, 2, 7 | Days | - | - | In [1, 2, 7] | Review interval frequency for ordering |
| `opened_date` | date | Yes | YYYY-MM-DD | Date | - | - | Valid ISO date | Date facility opened for operations |

---

## Entity: `Supplier` (Table: `suppliers`)
**Cardinality & Relationships:** 1:N with SupplierSKU, LeadTimeObservation, PurchaseRecommendation
**Lifecycle States:** `ACTIVE, ON_PROBATION, SUSPENDED`

| Field Name | Type | Req | Allowed Values | Units | PK | FK Reference | Validation Rule | Description |
|---|---|---|---|---|---|---|---|---|
| `supplier_id` | string | Yes | Regex: SUPP-[0-9]{4} | ID | PK | - | Must match SUPP-XXXX and be unique | Primary key for external vendor |
| `supplier_name` | string | Yes | Any non-empty string | Text | - | - | Length between 3 and 100 characters | Legal commercial vendor name |
| `tier` | string | Yes | TIER_1, TIER_2, TIER_3 | Enum | - | - | Must match tier enum | Strategic vendor classification tier |
| `reliability_score` | float | Yes | 0.50 - 1.00 | Score | - | - | 0.0 <= score <= 1.0 | Historical On-Time In-Full fulfillment index |
| `payment_terms_days` | integer | Yes | 15, 30, 45, 60, 90 | Days | - | - | Positive integer | Standard commercial credit terms |
| `country` | string | Yes | ISO-3166-1 alpha-2 or standard name | Country | - | - | Valid 2-letter country code | Supplier headquarters country |

---

## Entity: `SupplierSKU` (Table: `supplier_skus`)
**Cardinality & Relationships:** N:M Bridge table between Supplier (1:N) and SKU (1:N). 1:N with LeadTimeObservation
**Lifecycle States:** `ACTIVE, INACTIVE`

| Field Name | Type | Req | Allowed Values | Units | PK | FK Reference | Validation Rule | Description |
|---|---|---|---|---|---|---|---|---|
| `supplier_sku_id` | string | Yes | Regex: SSKU-SUPP-[0-9]{4}-SKU-[0-9]{6} | ID | PK | - | Unique compound bridge ID | Primary key for vendor-SKU contract relation |
| `supplier_id` | string | Yes | Regex: SUPP-[0-9]{4} | ID | - | Supplier.supplier_id | Must reference existing Supplier | Foreign key to vendor entity |
| `sku_id` | string | Yes | Regex: SKU-[0-9]{6} | ID | - | SKU.sku_id | Must reference existing SKU | Foreign key to SKU entity |
| `pack_size` | integer | Yes | 1, 6, 12, 24, 48, 96 | Units/Pack | - | - | Positive integer >= 1 | Master carton case pack multiple |
| `moq_units` | integer | Yes | >= pack_size | Units | - | - | Must be positive integer and multiple of pack_size | Minimum order quantity in units |
| `unit_purchase_cost` | float | Yes | >= 0.01 | USD ($) | - | - | Must be positive decimal | Negotiated contract unit procurement cost |
| `nominal_lead_time_days` | integer | Yes | 1 - 60 | Days | - | - | Positive integer >= 1 | Expected supplier order fulfillment duration |
| `lead_time_std_days` | float | Yes | 0.1 - 10.0 | Days | - | - | Non-negative float | Standard deviation of delivery lead times |
| `is_primary` | boolean | Yes | True, False | Boolean | - | - | Exactly one primary supplier per SKU | Indicator for primary source of supply |
| `effective_from` | date | Yes | YYYY-MM-DD | Date | - | - | Valid ISO date | Contract start validity date |
| `effective_to` | date | No | YYYY-MM-DD or NULL | Date | - | - | ISO date >= effective_from if present | Contract expiration validity date |

---

## Entity: `SalesHistory` (Table: `sales_history`)
**Cardinality & Relationships:** N:1 with Store, N:1 with SKU. Daily transactions / demand log

| Field Name | Type | Req | Allowed Values | Units | PK | FK Reference | Validation Rule | Description |
|---|---|---|---|---|---|---|---|---|
| `sale_id` | string | Yes | SALE-<store-id>-<sku-id>-<date> | ID | PK | - | Unique composite key format SALE-STORE-XXXXXX-SKU-XXXXXX-YYYY-MM-DD | Primary transaction record key |
| `store_id` | string | Yes | Regex: STORE-[0-9]{6} | ID | - | Store.store_id | Must exist in Store | Foreign key to Store |
| `sku_id` | string | Yes | Regex: SKU-[0-9]{6} | ID | - | SKU.sku_id | Must exist in SKU | Foreign key to SKU |
| `date` | date | Yes | YYYY-MM-DD | Date | - | - | Valid ISO date within observation window | Transaction calendar date |
| `units_sold` | integer | Yes | >= 0 | Units | - | - | Integer >= 0. Must be 0 if stockout occurred at day start | Actual recorded physical sales transactions |
| `promotion_flag` | boolean | Yes | True, False | Boolean | - | - | Boolean indicator | Whether promotional event/flyer was active |
| `promo_discount_pct` | float | Yes | 0.00 - 0.50 | Percentage | - | - | 0.0 if promotion_flag is False, > 0 if True | Promotional price discount fraction |
| `stockout_flag` | boolean | Yes | True, False | Boolean | - | - | Boolean indicator | True if zero on-hand prevented full demand fulfillment |
| `unconstrained_demand_est` | float | Yes | >= units_sold | Units | - | - | Must be >= units_sold | True unconstrained demand before inventory censoring |
| `lost_sales_units` | float | Yes | >= 0.0 | Units | - | - | Equals unconstrained_demand_est - units_sold | Sales lost due to stockout censoring |
| `unit_selling_price` | float | Yes | >= 0.01 | USD ($) | - | - | Positive float | Actual price charged per unit after discount |
| `gross_revenue` | float | Yes | >= 0.0 | USD ($) | - | - | Equals units_sold * unit_selling_price | Total gross transaction sales revenue |

---

## Entity: `InventorySnapshot` (Table: `inventory_snapshots`)
**Cardinality & Relationships:** N:1 with Store, N:1 with SKU. Daily end-of-day stock positions

| Field Name | Type | Req | Allowed Values | Units | PK | FK Reference | Validation Rule | Description |
|---|---|---|---|---|---|---|---|---|
| `snapshot_id` | string | Yes | INV-<store-id>-<sku-id>-<date> | ID | PK | - | Unique composite key format INV-STORE-XXXXXX-SKU-XXXXXX-YYYY-MM-DD | Primary daily snapshot record key |
| `store_id` | string | Yes | Regex: STORE-[0-9]{6} | ID | - | Store.store_id | Must exist in Store | Foreign key to Store |
| `sku_id` | string | Yes | Regex: SKU-[0-9]{6} | ID | - | SKU.sku_id | Must exist in SKU | Foreign key to SKU |
| `date` | date | Yes | YYYY-MM-DD | Date | - | - | Valid ISO date | Snapshot calendar date |
| `opening_on_hand_qty` | integer | Yes | >= 0 | Units | - | - | Non-negative integer | Stock on shelf/backroom at day start |
| `received_qty` | integer | Yes | >= 0 | Units | - | - | Non-negative integer | Stock delivered from POs during day |
| `units_sold` | integer | Yes | >= 0 | Units | - | - | Must match SalesHistory.units_sold | Stock depleted through sales |
| `closing_on_hand_qty` | integer | Yes | >= 0 | Units | - | - | Equals opening + received - units_sold | End of day physical stock on hand |
| `on_order_qty` | integer | Yes | >= 0 | Units | - | - | Non-negative integer | Stock in transit or committed on open purchase orders |
| `reserved_qty` | integer | Yes | >= 0 | Units | - | - | Non-negative integer <= closing_on_hand_qty | Stock allocated to pending customer click-and-collect |
| `available_qty` | integer | Yes | >= 0 | Units | - | - | Equals closing_on_hand + on_order - reserved | Effective net available stock position |
| `stockout_flag` | boolean | Yes | True, False | Boolean | - | - | True if closing_on_hand_qty == 0 | Binary indicator of zero stockout state |
| `days_of_supply` | float | Yes | >= 0.0 | Days | - | - | available_qty / max(daily_demand, 0.01) | Runway of stock based on average daily velocity |

---

## Entity: `LeadTimeObservation` (Table: `lead_time_observations`)
**Cardinality & Relationships:** N:1 with Supplier, N:1 with SKU, N:1 with SupplierSKU. Historical PO lead-time receipts
**Lifecycle States:** `ON_TIME, DELAYED, EARLY, CANCELLED`

| Field Name | Type | Req | Allowed Values | Units | PK | FK Reference | Validation Rule | Description |
|---|---|---|---|---|---|---|---|---|
| `observation_id` | string | Yes | Regex: LTO-[0-9]{6} | ID | PK | - | Unique zero-padded sequential ID | Primary key for lead time fulfillment event |
| `po_id` | string | Yes | Regex: PO-[0-9]{4}-[0-9]{6} | ID | - | PurchaseRecommendation.recommendation_id | References originating purchase order | Foreign key to purchase order |
| `supplier_id` | string | Yes | Regex: SUPP-[0-9]{4} | ID | - | Supplier.supplier_id | Must exist in Supplier | Foreign key to vendor |
| `sku_id` | string | Yes | Regex: SKU-[0-9]{6} | ID | - | SKU.sku_id | Must exist in SKU | Foreign key to SKU |
| `order_date` | date | Yes | YYYY-MM-DD | Date | - | - | Valid ISO date | Date PO was dispatched to vendor |
| `expected_delivery_date` | date | Yes | YYYY-MM-DD | Date | - | - | Must be >= order_date | Promised contract delivery arrival date |
| `actual_delivery_date` | date | Yes | YYYY-MM-DD | Date | - | - | Must be >= order_date (unless flagged anomalous) | Actual dock receipt date |
| `nominal_lead_time_days` | integer | Yes | >= 1 | Days | - | - | Positive integer | Contracted nominal lead time |
| `actual_lead_time_days` | integer | Yes | Any integer | Days | - | - | actual_delivery_date - order_date; >= 0 for valid rows | Empirical fulfillment days elapsed |
| `lead_time_variance_days` | integer | Yes | Any integer | Days | - | - | actual_lead_time_days - nominal_lead_time_days | Lateness vs nominal expectation |
| `status` | string | Yes | ON_TIME, DELAYED, EARLY, CANCELLED | Enum | - | - | Must match fulfillment status enum | Receipt punctuality classification |
| `delay_reason` | string | No | PORT_CONGESTION, FACTORY_DELAY, CARRIER_BREAKDOWN, WEATHER, NONE | Text | - | - | Optional text explanation | Root cause of fulfillment variance |

---

## Entity: `Forecast` (Table: `forecasts`)
**Cardinality & Relationships:** N:1 with Store, N:1 with SKU. Statistical demand projections per SKU-store

| Field Name | Type | Req | Allowed Values | Units | PK | FK Reference | Validation Rule | Description |
|---|---|---|---|---|---|---|---|---|
| `forecast_id` | string | Yes | Regex: FC-<store-id>-<sku-id>-<date> | ID | PK | - | Unique composite key format FC-STORE-XXXXXX-SKU-XXXXXX-YYYY-MM-DD | Primary demand forecast projection key |
| `store_id` | string | Yes | Regex: STORE-[0-9]{6} | ID | - | Store.store_id | Must exist in Store | Foreign key to Store |
| `sku_id` | string | Yes | Regex: SKU-[0-9]{6} | ID | - | SKU.sku_id | Must exist in SKU | Foreign key to SKU |
| `forecast_date` | date | Yes | YYYY-MM-DD | Date | - | - | Valid ISO date as-of forecast run | Date prediction was generated |
| `horizon_start_date` | date | Yes | YYYY-MM-DD | Date | - | - | Must be >= forecast_date | First day of prediction interval |
| `horizon_end_date` | date | Yes | YYYY-MM-DD | Date | - | - | Must be > horizon_start_date | Last day of prediction interval |
| `horizon_days` | integer | Yes | 7, 14, 30 | Days | - | - | Positive integer | Forecast lookahead horizon duration |
| `forecasted_daily_demand` | float | Yes | >= 0.0 | Units/Day | - | - | Non-negative float | Estimated mean daily unit velocity |
| `forecasted_daily_std` | float | Yes | >= 0.0 | Units/Day | - | - | Non-negative float | Estimated standard deviation of daily demand |
| `forecasted_total_horizon_demand` | float | Yes | >= 0.0 | Units | - | - | Equals forecasted_daily_demand * horizon_days | Integrated demand over entire horizon |
| `method` | string | Yes | HOLT_WINTERS, CROSTON_INTERMITTENT, EXPONENTIAL_SMOOTHING, UNCENSORED_MOVING_AVERAGE | Enum | - | - | Must match forecasting model enum | Statistical model used to generate estimate |
| `promo_uplift_factor` | float | Yes | >= 1.0 | Multiplier | - | - | Float >= 1.0 | Anticipated lift factor for planned promotions |
| `stockout_uncensored` | boolean | Yes | True, False | Boolean | - | - | Boolean indicator | Whether lost sales imputation was applied to training data |
| `created_at` | string | Yes | ISO-8601 Timestamp | Timestamp | - | - | Valid ISO-8601 timestamp | System timestamp when forecast was written |

---

## Entity: `ReorderPolicy` (Table: `reorder_policies`)
**Cardinality & Relationships:** 1:1 per SKU-Store active horizon. Governs replenishment triggers
**Lifecycle States:** `ACTIVE, REVISED, DEPRECATED`

| Field Name | Type | Req | Allowed Values | Units | PK | FK Reference | Validation Rule | Description |
|---|---|---|---|---|---|---|---|---|
| `policy_id` | string | Yes | Regex: RP-<store-id>-<sku-id> | ID | PK | - | Unique compound key format RP-STORE-XXXXXX-SKU-XXXXXX | Primary reorder parameterization key |
| `store_id` | string | Yes | Regex: STORE-[0-9]{6} | ID | - | Store.store_id | Must exist in Store | Foreign key to Store |
| `sku_id` | string | Yes | Regex: SKU-[0-9]{6} | ID | - | SKU.sku_id | Must exist in SKU | Foreign key to SKU |
| `service_level` | float | Yes | 0.85 - 0.999 | Ratio | - | - | Float between 0.80 and 0.999 | Target cycle service level probability (1 - Stockout Risk) |
| `z_factor` | float | Yes | 1.28 - 3.09 | Standard Score | - | - | Inverse standard normal CDF of service_level | Safety stock statistical multiplier |
| `effective_lead_time_days` | float | Yes | >= 1.0 | Days | - | - | Positive float | Mean supplier replenishment lead time |
| `lead_time_demand` | float | Yes | >= 0.0 | Units | - | - | Equals daily_demand * lead_time | Expected mean sales during fulfillment window |
| `safety_stock_units` | integer | Yes | >= 0 | Units | - | - | Z * sqrt(L * std_d^2 + d^2 * std_L^2) | Buffer stock protecting against demand & lead time variance |
| `reorder_point_units` | integer | Yes | >= safety_stock_units | Units | - | - | Equals lead_time_demand + safety_stock_units | Inventory position threshold triggering replenishment order |
| `target_stock_level` | integer | Yes | >= reorder_point_units | Units | - | - | Equals ROP + (ReviewPeriod * daily_demand) | Order-up-to stock target ceiling |
| `review_period_days` | integer | Yes | 1 - 14 | Days | - | - | Positive integer | Frequency of replenishment review in days |
| `max_store_capacity_units` | integer | Yes | >= 10 | Units | - | - | Positive integer | Hard shelf/backroom allocation ceiling for this SKU-store |
| `last_updated` | date | Yes | YYYY-MM-DD | Date | - | - | Valid ISO date | Date policy parameters were recalculated |

---

## Entity: `PurchaseRecommendation` (Table: `purchase_recommendations`)
**Cardinality & Relationships:** N:1 with Store, N:1 with SKU, N:1 with Supplier. 1:N with OrderLifecycleEvent
**Lifecycle States:** `RECOMMENDED, APPROVED, REJECTED, EXCEPTION_FLAGGED, ORDERED`

| Field Name | Type | Req | Allowed Values | Units | PK | FK Reference | Validation Rule | Description |
|---|---|---|---|---|---|---|---|---|
| `recommendation_id` | string | Yes | Regex: PO-[0-9]{4}-[0-9]{6} | ID | PK | - | Unique sequential key format PO-YYYY-XXXXXX | Primary replenishment recommendation key |
| `store_id` | string | Yes | Regex: STORE-[0-9]{6} | ID | - | Store.store_id | Must exist in Store | Foreign key to destination facility |
| `sku_id` | string | Yes | Regex: SKU-[0-9]{6} | ID | - | SKU.sku_id | Must exist in SKU | Foreign key to replenishing item |
| `supplier_id` | string | Yes | Regex: SUPP-[0-9]{4} | ID | - | Supplier.supplier_id | Must exist in Supplier | Foreign key to vendor providing goods |
| `recommendation_date` | date | Yes | YYYY-MM-DD | Date | - | - | Valid ISO date | Date recommendation was generated by engine |
| `current_on_hand_qty` | integer | Yes | >= 0 | Units | - | - | Current physical stock | On-hand inventory at recommendation time |
| `current_on_order_qty` | integer | Yes | >= 0 | Units | - | - | Open pipeline stock | Inventory already on order with supplier |
| `current_reserved_qty` | integer | Yes | >= 0 | Units | - | - | Committed orders | Inventory committed to pending fulfillments |
| `net_inventory_position` | integer | Yes | Any integer | Units | - | - | on_hand + on_order - reserved | Effective net stock position |
| `reorder_point` | integer | Yes | >= 0 | Units | - | - | From ReorderPolicy | Trigger threshold for ordering |
| `target_stock_level` | integer | Yes | >= reorder_point | Units | - | - | From ReorderPolicy | Target order-up-to level |
| `gross_need_units` | integer | Yes | >= 0 | Units | - | - | max(0, target_stock_level - net_inventory_position) | Deficit needed to reach target stock level |
| `unrounded_order_qty` | integer | Yes | >= 0 | Units | - | - | max(gross_need, MOQ) if gross_need > 0 else 0 | Required order quantity before pack-size rounding |
| `pack_size_applied` | integer | Yes | >= 1 | Units/Pack | - | - | Contract supplier pack size | Pack size multiple applied for rounding |
| `moq_applied` | integer | Yes | >= 0 | Units | - | - | Contract minimum order quantity | Vendor MOQ applied |
| `capacity_constrained_qty` | integer | Yes | >= 0 | Units | - | - | Order quantity respecting store storage limits | Quantity capped by store backroom/shelf capacity |
| `final_order_qty` | integer | Yes | >= 0 | Units | - | - | Must be multiple of pack_size and >= MOQ if ordered, unless exception | Recommended final unit order quantity |
| `unit_cost` | float | Yes | >= 0.01 | USD ($) | - | - | Procurement unit contract cost | Purchase cost per unit |
| `total_cost` | float | Yes | >= 0.0 | USD ($) | - | - | final_order_qty * unit_cost | Total financial commitment for this purchase recommendation |
| `priority` | string | Yes | CRITICAL_STOCKOUT, HIGH_RISK, ROUTINE, SEASONAL_BUILD | Enum | - | - | Must match priority enum | Urgency level for operational review |
| `status` | string | Yes | RECOMMENDED, APPROVED, REJECTED, EXCEPTION_FLAGGED, ORDERED | Enum | - | - | Must match recommendation status enum | Current state in approval lifecycle |
| `exception_code` | string | Yes | NONE, ERR_DISCONTINUED_SKU, ERR_CAPACITY_EXCEEDED, ERR_PACK_SIZE_MISMATCH, ERR_NEGATIVE_LEAD_TIME, ERR_SUPPLIER_INACTIVE | Enum | - | - | Must match exception enum | Audit error code if rule condition violated |
| `rationale` | string | Yes | Any explanatory text | Text | - | - | Detailed transparent explanation | Plain language operational justification and math trace |
| `created_at` | string | Yes | ISO-8601 Timestamp | Timestamp | - | - | Valid ISO-8601 timestamp | Record creation timestamp |

---

## Entity: `OrderLifecycleEvent` (Table: `order_lifecycle_events`)
**Cardinality & Relationships:** N:1 with PurchaseRecommendation. Audit trail preserving state transitions

| Field Name | Type | Req | Allowed Values | Units | PK | FK Reference | Validation Rule | Description |
|---|---|---|---|---|---|---|---|---|
| `event_id` | string | Yes | Regex: EVT-[0-9]{6} | ID | PK | - | Unique sequential key format EVT-XXXXXX | Primary key for event audit record |
| `recommendation_id` | string | Yes | Regex: PO-[0-9]{4}-[0-9]{6} | ID | - | PurchaseRecommendation.recommendation_id | Must exist in PurchaseRecommendation | Foreign key to recommendation |
| `from_status` | string | Yes | Any status or NONE | Enum | - | - | Prior state in lifecycle | Previous recommendation state |
| `to_status` | string | Yes | RECOMMENDED, APPROVED, REJECTED, EXCEPTION_FLAGGED, ORDERED | Enum | - | - | Valid recommendation lifecycle state | New recommendation state |
| `actor` | string | Yes | System/ReplenishmentEngine, StoreManager, MerchandisingAnalyst, OperationsManager | Role | - | - | Authorized user or system role | Actor who triggered the state change |
| `action` | string | Yes | GENERATE, APPROVE, OVERRIDE_QTY, REJECT, DISPATCH, ESCALATE | Action | - | - | Business action verb | Action performed on recommendation |
| `notes` | string | Yes | Audit text log | Text | - | - | Audit comments or system decision reasoning | Explanatory remarks accompanying state transition |
| `timestamp` | string | Yes | ISO-8601 Timestamp | Timestamp | - | - | Valid ISO-8601 timestamp | Wall clock timestamp of event occurrence |

---
