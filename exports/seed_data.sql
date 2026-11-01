-- ============================================================================
-- SKU-Location Demand Forecasting & Replenishment Engine DDL Schema
-- Auto-generated from Data Dictionary Specifications
-- ============================================================================

DROP TABLE IF EXISTS skus CASCADE;
CREATE TABLE skus (
    sku_id VARCHAR(255) NOT NULL,
    sku_name VARCHAR(255) NOT NULL,
    category VARCHAR(255) NOT NULL,
    unit_cost NUMERIC(14, 4) NOT NULL,
    unit_price NUMERIC(14, 4) NOT NULL,
    unit_volume_m3 NUMERIC(14, 4) NOT NULL,
    unit_weight_kg NUMERIC(14, 4) NOT NULL,
    status VARCHAR(255) NOT NULL,
    launch_date DATE NOT NULL,
    discontinue_date DATE NULL,
    CONSTRAINT pk_skus PRIMARY KEY (sku_id)
);


DROP TABLE IF EXISTS stores CASCADE;
CREATE TABLE stores (
    store_id VARCHAR(255) NOT NULL,
    store_name VARCHAR(255) NOT NULL,
    channel VARCHAR(255) NOT NULL,
    region VARCHAR(255) NOT NULL,
    max_storage_units INTEGER NOT NULL,
    max_storage_volume_m3 NUMERIC(14, 4) NOT NULL,
    replenishment_cadence_days INTEGER NOT NULL,
    opened_date DATE NOT NULL,
    CONSTRAINT pk_stores PRIMARY KEY (store_id)
);


DROP TABLE IF EXISTS suppliers CASCADE;
CREATE TABLE suppliers (
    supplier_id VARCHAR(255) NOT NULL,
    supplier_name VARCHAR(255) NOT NULL,
    tier VARCHAR(255) NOT NULL,
    reliability_score NUMERIC(14, 4) NOT NULL,
    payment_terms_days INTEGER NOT NULL,
    country VARCHAR(255) NOT NULL,
    CONSTRAINT pk_suppliers PRIMARY KEY (supplier_id)
);


DROP TABLE IF EXISTS supplier_skus CASCADE;
CREATE TABLE supplier_skus (
    supplier_sku_id VARCHAR(255) NOT NULL,
    supplier_id VARCHAR(255) NOT NULL,
    sku_id VARCHAR(255) NOT NULL,
    pack_size INTEGER NOT NULL,
    moq_units INTEGER NOT NULL,
    unit_purchase_cost NUMERIC(14, 4) NOT NULL,
    nominal_lead_time_days INTEGER NOT NULL,
    lead_time_std_days NUMERIC(14, 4) NOT NULL,
    is_primary BOOLEAN NOT NULL,
    effective_from DATE NOT NULL,
    effective_to DATE NULL,
    CONSTRAINT pk_supplier_skus PRIMARY KEY (supplier_sku_id),
    CONSTRAINT fk_supplier_skus_supplier_id FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id),
    CONSTRAINT fk_supplier_skus_sku_id FOREIGN KEY (sku_id) REFERENCES skus(sku_id)
);

CREATE INDEX idx_supplier_skus_supplier_id ON supplier_skus(supplier_id);
CREATE INDEX idx_supplier_skus_sku_id ON supplier_skus(sku_id);

DROP TABLE IF EXISTS sales_history CASCADE;
CREATE TABLE sales_history (
    sale_id VARCHAR(255) NOT NULL,
    store_id VARCHAR(255) NOT NULL,
    sku_id VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    units_sold INTEGER NOT NULL,
    promotion_flag BOOLEAN NOT NULL,
    promo_discount_pct NUMERIC(14, 4) NOT NULL,
    stockout_flag BOOLEAN NOT NULL,
    unconstrained_demand_est NUMERIC(14, 4) NOT NULL,
    lost_sales_units NUMERIC(14, 4) NOT NULL,
    unit_selling_price NUMERIC(14, 4) NOT NULL,
    gross_revenue NUMERIC(14, 4) NOT NULL,
    CONSTRAINT pk_sales_history PRIMARY KEY (sale_id),
    CONSTRAINT fk_sales_history_store_id FOREIGN KEY (store_id) REFERENCES stores(store_id),
    CONSTRAINT fk_sales_history_sku_id FOREIGN KEY (sku_id) REFERENCES skus(sku_id)
);

CREATE INDEX idx_sales_history_store_id ON sales_history(store_id);
CREATE INDEX idx_sales_history_sku_id ON sales_history(sku_id);

DROP TABLE IF EXISTS inventory_snapshots CASCADE;
CREATE TABLE inventory_snapshots (
    snapshot_id VARCHAR(255) NOT NULL,
    store_id VARCHAR(255) NOT NULL,
    sku_id VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    opening_on_hand_qty INTEGER NOT NULL,
    received_qty INTEGER NOT NULL,
    units_sold INTEGER NOT NULL,
    closing_on_hand_qty INTEGER NOT NULL,
    on_order_qty INTEGER NOT NULL,
    reserved_qty INTEGER NOT NULL,
    available_qty INTEGER NOT NULL,
    stockout_flag BOOLEAN NOT NULL,
    days_of_supply NUMERIC(14, 4) NOT NULL,
    CONSTRAINT pk_inventory_snapshots PRIMARY KEY (snapshot_id),
    CONSTRAINT fk_inventory_snapshots_store_id FOREIGN KEY (store_id) REFERENCES stores(store_id),
    CONSTRAINT fk_inventory_snapshots_sku_id FOREIGN KEY (sku_id) REFERENCES skus(sku_id)
);

CREATE INDEX idx_inventory_snapshots_store_id ON inventory_snapshots(store_id);
CREATE INDEX idx_inventory_snapshots_sku_id ON inventory_snapshots(sku_id);

DROP TABLE IF EXISTS lead_time_observations CASCADE;
CREATE TABLE lead_time_observations (
    observation_id VARCHAR(255) NOT NULL,
    po_id VARCHAR(255) NOT NULL,
    supplier_id VARCHAR(255) NOT NULL,
    sku_id VARCHAR(255) NOT NULL,
    order_date DATE NOT NULL,
    expected_delivery_date DATE NOT NULL,
    actual_delivery_date DATE NOT NULL,
    nominal_lead_time_days INTEGER NOT NULL,
    actual_lead_time_days INTEGER NOT NULL,
    lead_time_variance_days INTEGER NOT NULL,
    status VARCHAR(255) NOT NULL,
    delay_reason VARCHAR(255) NULL,
    CONSTRAINT pk_lead_time_observations PRIMARY KEY (observation_id),
    CONSTRAINT fk_lead_time_observations_po_id FOREIGN KEY (po_id) REFERENCES purchase_recommendations(recommendation_id),
    CONSTRAINT fk_lead_time_observations_supplier_id FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id),
    CONSTRAINT fk_lead_time_observations_sku_id FOREIGN KEY (sku_id) REFERENCES skus(sku_id)
);

CREATE INDEX idx_lead_time_observations_po_id ON lead_time_observations(po_id);
CREATE INDEX idx_lead_time_observations_supplier_id ON lead_time_observations(supplier_id);
CREATE INDEX idx_lead_time_observations_sku_id ON lead_time_observations(sku_id);

DROP TABLE IF EXISTS forecasts CASCADE;
CREATE TABLE forecasts (
    forecast_id VARCHAR(255) NOT NULL,
    store_id VARCHAR(255) NOT NULL,
    sku_id VARCHAR(255) NOT NULL,
    forecast_date DATE NOT NULL,
    horizon_start_date DATE NOT NULL,
    horizon_end_date DATE NOT NULL,
    horizon_days INTEGER NOT NULL,
    forecasted_daily_demand NUMERIC(14, 4) NOT NULL,
    forecasted_daily_std NUMERIC(14, 4) NOT NULL,
    forecasted_total_horizon_demand NUMERIC(14, 4) NOT NULL,
    method VARCHAR(255) NOT NULL,
    promo_uplift_factor NUMERIC(14, 4) NOT NULL,
    stockout_uncensored BOOLEAN NOT NULL,
    created_at VARCHAR(255) NOT NULL,
    CONSTRAINT pk_forecasts PRIMARY KEY (forecast_id),
    CONSTRAINT fk_forecasts_store_id FOREIGN KEY (store_id) REFERENCES stores(store_id),
    CONSTRAINT fk_forecasts_sku_id FOREIGN KEY (sku_id) REFERENCES skus(sku_id)
);

CREATE INDEX idx_forecasts_store_id ON forecasts(store_id);
CREATE INDEX idx_forecasts_sku_id ON forecasts(sku_id);

DROP TABLE IF EXISTS reorder_policies CASCADE;
CREATE TABLE reorder_policies (
    policy_id VARCHAR(255) NOT NULL,
    store_id VARCHAR(255) NOT NULL,
    sku_id VARCHAR(255) NOT NULL,
    service_level NUMERIC(14, 4) NOT NULL,
    z_factor NUMERIC(14, 4) NOT NULL,
    effective_lead_time_days NUMERIC(14, 4) NOT NULL,
    lead_time_demand NUMERIC(14, 4) NOT NULL,
    safety_stock_units INTEGER NOT NULL,
    reorder_point_units INTEGER NOT NULL,
    target_stock_level INTEGER NOT NULL,
    review_period_days INTEGER NOT NULL,
    max_store_capacity_units INTEGER NOT NULL,
    last_updated DATE NOT NULL,
    CONSTRAINT pk_reorder_policies PRIMARY KEY (policy_id),
    CONSTRAINT fk_reorder_policies_store_id FOREIGN KEY (store_id) REFERENCES stores(store_id),
    CONSTRAINT fk_reorder_policies_sku_id FOREIGN KEY (sku_id) REFERENCES skus(sku_id)
);

CREATE INDEX idx_reorder_policies_store_id ON reorder_policies(store_id);
CREATE INDEX idx_reorder_policies_sku_id ON reorder_policies(sku_id);

DROP TABLE IF EXISTS purchase_recommendations CASCADE;
CREATE TABLE purchase_recommendations (
    recommendation_id VARCHAR(255) NOT NULL,
    store_id VARCHAR(255) NOT NULL,
    sku_id VARCHAR(255) NOT NULL,
    supplier_id VARCHAR(255) NOT NULL,
    recommendation_date DATE NOT NULL,
    current_on_hand_qty INTEGER NOT NULL,
    current_on_order_qty INTEGER NOT NULL,
    current_reserved_qty INTEGER NOT NULL,
    net_inventory_position INTEGER NOT NULL,
    reorder_point INTEGER NOT NULL,
    target_stock_level INTEGER NOT NULL,
    gross_need_units INTEGER NOT NULL,
    unrounded_order_qty INTEGER NOT NULL,
    pack_size_applied INTEGER NOT NULL,
    moq_applied INTEGER NOT NULL,
    capacity_constrained_qty INTEGER NOT NULL,
    final_order_qty INTEGER NOT NULL,
    unit_cost NUMERIC(14, 4) NOT NULL,
    total_cost NUMERIC(14, 4) NOT NULL,
    priority VARCHAR(255) NOT NULL,
    status VARCHAR(255) NOT NULL,
    exception_code VARCHAR(255) NOT NULL,
    rationale VARCHAR(255) NOT NULL,
    created_at VARCHAR(255) NOT NULL,
    CONSTRAINT pk_purchase_recommendations PRIMARY KEY (recommendation_id),
    CONSTRAINT fk_purchase_recommendations_store_id FOREIGN KEY (store_id) REFERENCES stores(store_id),
    CONSTRAINT fk_purchase_recommendations_sku_id FOREIGN KEY (sku_id) REFERENCES skus(sku_id),
    CONSTRAINT fk_purchase_recommendations_supplier_id FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
);

CREATE INDEX idx_purchase_recommendations_store_id ON purchase_recommendations(store_id);
CREATE INDEX idx_purchase_recommendations_sku_id ON purchase_recommendations(sku_id);
CREATE INDEX idx_purchase_recommendations_supplier_id ON purchase_recommendations(supplier_id);

DROP TABLE IF EXISTS order_lifecycle_events CASCADE;
CREATE TABLE order_lifecycle_events (
    event_id VARCHAR(255) NOT NULL,
    recommendation_id VARCHAR(255) NOT NULL,
    from_status VARCHAR(255) NOT NULL,
    to_status VARCHAR(255) NOT NULL,
    actor VARCHAR(255) NOT NULL,
    action VARCHAR(255) NOT NULL,
    notes VARCHAR(255) NOT NULL,
    timestamp VARCHAR(255) NOT NULL,
    CONSTRAINT pk_order_lifecycle_events PRIMARY KEY (event_id),
    CONSTRAINT fk_order_lifecycle_events_recommendation_id FOREIGN KEY (recommendation_id) REFERENCES purchase_recommendations(recommendation_id)
);

CREATE INDEX idx_order_lifecycle_events_recommendation_id ON order_lifecycle_events(recommendation_id);

-- ============================================================================
-- Seed Insert Statements
-- ============================================================================

-- Inserts for skus
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000001', 'Produce Item 0001', 'Produce', 2.09, 3.72, 0.0042, 0.91, 'ACTIVE', '2025-01-21', NULL);
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000002', 'Pantry Item 0002', 'Pantry', 9.31, 17.02, 0.0047, 2.87, 'ACTIVE', '2025-01-04', NULL);
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000003', 'Dairy Item 0003', 'Dairy', 1.54, 2.18, 0.0032, 0.76, 'ACTIVE', '2025-01-19', NULL);
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000004', 'Produce Item 0004', 'Produce', 1.31, 2.17, 0.0031, 0.21, 'ACTIVE', '2025-01-13', NULL);
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000005', 'Dairy Item 0005', 'Dairy', 2.5, 3.63, 0.0046, 1.03, 'ACTIVE', '2025-01-10', NULL);
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000006', 'Beverages Item 0006', 'Beverages', 3.86, 6.8, 0.0022, 1.06, 'ACTIVE', '2025-01-14', NULL);
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000007', 'Produce Item 0007', 'Produce', 2.08, 3.02, 0.0016, 1.35, 'ACTIVE', '2025-01-07', NULL);
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000008', 'Pantry Item 0008', 'Pantry', 4.01, 6.04, 0.0063, 2.44, 'ACTIVE', '2025-01-08', NULL);
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000009', 'Produce Item 0009', 'Produce', 2.93, 4.41, 0.0023, 1.31, 'ACTIVE', '2025-01-22', NULL);
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000010', 'Beverages Item 0010', 'Beverages', 1.18, 1.84, 0.0048, 0.94, 'ACTIVE', '2025-01-15', NULL);
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000011', 'Produce Item 0011', 'Produce', 3.12, 4.41, 0.0021, 1.39, 'ACTIVE', '2025-01-02', NULL);
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000012', 'Household Item 0012', 'Household', 14.36, 21.76, 0.0134, 3.44, 'ACTIVE', '2025-01-09', NULL);
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000013', 'Pantry Item 0013', 'Pantry', 10.07, 16.95, 0.0064, 0.62, 'ACTIVE', '2025-01-02', NULL);
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000014', 'Frozen Item 0014', 'Frozen', 4.51, 6.66, 0.0039, 1.48, 'ACTIVE', '2025-01-14', NULL);
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000015', 'Frozen Item 0015', 'Frozen', 3.59, 6.08, 0.0034, 2.62, 'ACTIVE', '2025-01-10', NULL);
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000016', 'Dairy Item 0016', 'Dairy', 1.72, 2.6, 0.0047, 1.46, 'ACTIVE', '2025-01-09', NULL);
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000017', 'Produce Item 0017', 'Produce', 2.17, 3.52, 0.0032, 0.21, 'ACTIVE', '2025-01-07', NULL);
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000018', 'Pantry Item 0018', 'Pantry', 3.28, 5.69, 0.003, 2.44, 'ACTIVE', '2025-01-01', NULL);
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000019', 'Produce Item 0019', 'Produce', 2.58, 3.81, 0.0043, 0.44, 'ACTIVE', '2025-01-06', NULL);
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000020', 'Personal Care Item 0020', 'Personal Care', 14.47, 27.29, 0.0087, 2.75, 'ACTIVE', '2025-01-12', NULL);
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000021', 'Frozen Item 0021', 'Frozen', 5.89, 9.59, 0.0075, 0.94, 'ACTIVE', '2025-01-18', NULL);
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000022', 'Bakery Item 0022', 'Bakery', 1.15, 1.52, 0.0022, 0.62, 'PHASE_OUT', '2025-01-22', '2025-03-12');
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000023', 'Personal Care Item 0023', 'Personal Care', 12.01, 24.88, 0.0041, 2.35, 'ACTIVE', '2025-01-13', NULL);
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000024', 'Pantry Item 0024', 'Pantry', 9.4, 13.41, 0.0075, 1.58, 'PHASE_OUT', '2025-01-04', '2025-02-19');
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000025', 'Frozen Item 0025', 'Frozen', 5.43, 9.16, 0.0025, 2.18, 'DISCONTINUED', '2025-01-12', '2025-02-01');
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000026', 'Pantry Item 0026', 'Pantry', 4.75, 8.25, 0.0062, 1.76, 'PHASE_OUT', '2025-01-01', '2025-02-26');
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000027', 'Dairy Item 0027', 'Dairy', 2.08, 3.35, 0.0039, 0.62, 'ACTIVE', '2025-01-18', NULL);
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000028', 'Household Item 0028', 'Household', 20.55, 39.38, 0.0088, 1.87, 'ACTIVE', '2025-01-12', NULL);
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000029', 'Bakery Item 0029', 'Bakery', 2.87, 5.16, 0.0028, 0.64, 'PHASE_OUT', '2025-01-17', '2025-03-16');
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000030', 'Dairy Item 0030', 'Dairy', 4.18, 5.89, 0.003, 0.85, 'ACTIVE', '2025-01-06', NULL);
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000031', 'Bakery Item 0031', 'Bakery', 2.33, 3.91, 0.0033, 1.18, 'ACTIVE', '2025-01-22', NULL);
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000032', 'Produce Item 0032', 'Produce', 2.05, 3.33, 0.0012, 0.36, 'ACTIVE', '2025-01-20', NULL);
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000033', 'Household Item 0033', 'Household', 15.69, 25.29, 0.0084, 2.05, 'PHASE_OUT', '2025-01-06', '2025-03-21');
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000034', 'Household Item 0034', 'Household', 15.39, 34.25, 0.0102, 1.21, 'ACTIVE', '2025-01-08', NULL);
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000035', 'Bakery Item 0035', 'Bakery', 0.91, 1.39, 0.0013, 0.39, 'ACTIVE', '2025-01-19', NULL);
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000036', 'Household Item 0036', 'Household', 11.52, 23.03, 0.003, 2.78, 'ACTIVE', '2025-01-04', NULL);
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000037', 'Beverages Item 0037', 'Beverages', 3.41, 4.6, 0.0035, 1.05, 'ACTIVE', '2025-01-17', NULL);
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000038', 'Dairy Item 0038', 'Dairy', 4.95, 6.53, 0.0032, 1.83, 'ACTIVE', '2025-01-12', NULL);
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000039', 'Dairy Item 0039', 'Dairy', 3.33, 4.8, 0.0043, 1.89, 'ACTIVE', '2025-01-09', NULL);
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000040', 'Dairy Item 0040', 'Dairy', 1.72, 3.08, 0.0011, 0.96, 'ACTIVE', '2025-01-02', NULL);
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000041', 'Personal Care Item 0041', 'Personal Care', 23.48, 44.0, 0.0099, 2.8, 'ACTIVE', '2025-01-22', NULL);
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000042', 'Bakery Item 0042', 'Bakery', 0.83, 1.2, 0.0024, 1.69, 'DISCONTINUED', '2025-01-07', '2025-02-14');
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000043', 'Bakery Item 0043', 'Bakery', 1.09, 1.52, 0.0033, 0.84, 'ACTIVE', '2025-01-12', NULL);
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000044', 'Bakery Item 0044', 'Bakery', 1.97, 3.5, 0.0043, 1.53, 'ACTIVE', '2025-01-15', NULL);
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000045', 'Household Item 0045', 'Household', 13.6, 32.03, 0.0105, 3.87, 'ACTIVE', '2025-01-05', NULL);
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000046', 'Beverages Item 0046', 'Beverages', 3.87, 6.66, 0.0013, 1.15, 'ACTIVE', '2025-01-11', NULL);
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000047', 'Dairy Item 0047', 'Dairy', 4.96, 6.83, 0.0041, 1.23, 'ACTIVE', '2025-01-20', NULL);
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000048', 'Household Item 0048', 'Household', 19.7, 46.21, 0.0108, 2.74, 'ACTIVE', '2025-01-13', NULL);
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000049', 'Bakery Item 0049', 'Bakery', 2.34, 4.14, 0.0014, 0.65, 'ACTIVE', '2025-01-17', NULL);
INSERT INTO skus (sku_id, sku_name, category, unit_cost, unit_price, unit_volume_m3, unit_weight_kg, status, launch_date, discontinue_date) VALUES ('SKU-000050', 'Personal Care Item 0050', 'Personal Care', 6.65, 13.63, 0.0057, 0.71, 'ACTIVE', '2025-01-06', NULL);

-- Inserts for stores
INSERT INTO stores (store_id, store_name, channel, region, max_storage_units, max_storage_volume_m3, replenishment_cadence_days, opened_date) VALUES ('STORE-000001', 'Central Retail Supermarket 001', 'RETAIL_SUPERMARKET', 'Central', 26471, 158.83, 1, '2022-11-29');
INSERT INTO stores (store_id, store_name, channel, region, max_storage_units, max_storage_volume_m3, replenishment_cadence_days, opened_date) VALUES ('STORE-000002', 'East Regional Dc 002', 'REGIONAL_DC', 'East', 125929, 1007.43, 1, '2020-12-05');
INSERT INTO stores (store_id, store_name, channel, region, max_storage_units, max_storage_volume_m3, replenishment_cadence_days, opened_date) VALUES ('STORE-000003', 'East Retail Supermarket 003', 'RETAIL_SUPERMARKET', 'East', 30279, 181.67, 2, '2023-07-13');
INSERT INTO stores (store_id, store_name, channel, region, max_storage_units, max_storage_volume_m3, replenishment_cadence_days, opened_date) VALUES ('STORE-000004', 'East Retail Supermarket 004', 'RETAIL_SUPERMARKET', 'East', 12380, 74.28, 1, '2023-04-19');
INSERT INTO stores (store_id, store_name, channel, region, max_storage_units, max_storage_volume_m3, replenishment_cadence_days, opened_date) VALUES ('STORE-000005', 'North Retail Supermarket 005', 'RETAIL_SUPERMARKET', 'North', 10002, 60.01, 2, '2023-04-26');

-- Inserts for suppliers
INSERT INTO suppliers (supplier_id, supplier_name, tier, reliability_score, payment_terms_days, country) VALUES ('SUPP-0001', 'Vendor Partner 001 (TIER_1)', 'TIER_1', 0.98, 30, 'DE');
INSERT INTO suppliers (supplier_id, supplier_name, tier, reliability_score, payment_terms_days, country) VALUES ('SUPP-0002', 'Vendor Partner 002 (TIER_2)', 'TIER_2', 0.92, 60, 'CA');
INSERT INTO suppliers (supplier_id, supplier_name, tier, reliability_score, payment_terms_days, country) VALUES ('SUPP-0003', 'Vendor Partner 003 (TIER_2)', 'TIER_2', 0.81, 45, 'CA');
INSERT INTO suppliers (supplier_id, supplier_name, tier, reliability_score, payment_terms_days, country) VALUES ('SUPP-0004', 'Vendor Partner 004 (TIER_2)', 'TIER_2', 0.87, 30, 'US');
INSERT INTO suppliers (supplier_id, supplier_name, tier, reliability_score, payment_terms_days, country) VALUES ('SUPP-0005', 'Vendor Partner 005 (TIER_2)', 'TIER_2', 0.83, 60, 'MX');
INSERT INTO suppliers (supplier_id, supplier_name, tier, reliability_score, payment_terms_days, country) VALUES ('SUPP-0006', 'Vendor Partner 006 (TIER_2)', 'TIER_2', 0.89, 30, 'CA');
INSERT INTO suppliers (supplier_id, supplier_name, tier, reliability_score, payment_terms_days, country) VALUES ('SUPP-0007', 'Vendor Partner 007 (TIER_2)', 'TIER_2', 0.74, 45, 'US');
INSERT INTO suppliers (supplier_id, supplier_name, tier, reliability_score, payment_terms_days, country) VALUES ('SUPP-0008', 'Vendor Partner 008 (TIER_3)', 'TIER_3', 0.86, 30, 'VN');
INSERT INTO suppliers (supplier_id, supplier_name, tier, reliability_score, payment_terms_days, country) VALUES ('SUPP-0009', 'Vendor Partner 009 (TIER_1)', 'TIER_1', 0.84, 60, 'VN');
INSERT INTO suppliers (supplier_id, supplier_name, tier, reliability_score, payment_terms_days, country) VALUES ('SUPP-0010', 'Vendor Partner 010 (TIER_1)', 'TIER_1', 0.92, 45, 'US');

-- Inserts for supplier_skus
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0002-SKU-000001', 'SUPP-0002', 'SKU-000001', 12, 48, 2.09, 6, 0.5, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0005-SKU-000002', 'SUPP-0005', 'SKU-000002', 6, 6, 9.31, 6, 1.9, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0004-SKU-000003', 'SUPP-0004', 'SKU-000003', 12, 48, 1.54, 8, 0.5, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0007-SKU-000003', 'SUPP-0007', 'SKU-000003', 12, 36, 1.62, 9, 0.6, FALSE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0007-SKU-000004', 'SUPP-0007', 'SKU-000004', 24, 96, 1.31, 5, 1.5, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0003-SKU-000005', 'SUPP-0003', 'SKU-000005', 48, 192, 2.5, 11, 1.8, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0010-SKU-000006', 'SUPP-0010', 'SKU-000006', 12, 12, 3.86, 8, 1.9, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0004-SKU-000007', 'SUPP-0004', 'SKU-000007', 12, 12, 2.08, 13, 1.6, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0010-SKU-000008', 'SUPP-0010', 'SKU-000008', 24, 96, 4.01, 9, 1.8, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0002-SKU-000009', 'SUPP-0002', 'SKU-000009', 24, 96, 2.93, 3, 1.3, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0008-SKU-000010', 'SUPP-0008', 'SKU-000010', 12, 48, 1.18, 8, 0.6, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0001-SKU-000011', 'SUPP-0001', 'SKU-000011', 48, 192, 3.12, 9, 1.7, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0002-SKU-000012', 'SUPP-0002', 'SKU-000012', 12, 12, 14.36, 8, 1.1, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0005-SKU-000012', 'SUPP-0005', 'SKU-000012', 12, 12, 15.08, 7, 1.3, FALSE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0005-SKU-000013', 'SUPP-0005', 'SKU-000013', 48, 96, 10.07, 10, 1.3, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0010-SKU-000013', 'SUPP-0010', 'SKU-000013', 48, 48, 10.57, 12, 1.6, FALSE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0005-SKU-000014', 'SUPP-0005', 'SKU-000014', 24, 48, 4.51, 7, 1.6, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0004-SKU-000015', 'SUPP-0004', 'SKU-000015', 24, 120, 3.59, 10, 1.5, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0008-SKU-000016', 'SUPP-0008', 'SKU-000016', 6, 12, 1.72, 8, 1.4, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0006-SKU-000016', 'SUPP-0006', 'SKU-000016', 6, 6, 1.81, 8, 1.7, FALSE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0009-SKU-000017', 'SUPP-0009', 'SKU-000017', 6, 12, 2.17, 6, 0.6, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0005-SKU-000018', 'SUPP-0005', 'SKU-000018', 12, 12, 3.28, 7, 0.7, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0003-SKU-000018', 'SUPP-0003', 'SKU-000018', 12, 12, 3.44, 7, 0.8, FALSE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0010-SKU-000019', 'SUPP-0010', 'SKU-000019', 6, 6, 2.58, 10, 1.4, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0001-SKU-000020', 'SUPP-0001', 'SKU-000020', 48, 240, 14.47, 12, 0.8, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0009-SKU-000021', 'SUPP-0009', 'SKU-000021', 12, 60, 5.89, 8, 1.9, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0008-SKU-000021', 'SUPP-0008', 'SKU-000021', 12, 48, 6.18, 8, 2.3, FALSE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0006-SKU-000022', 'SUPP-0006', 'SKU-000022', 12, 48, 1.15, 8, 1.4, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0008-SKU-000023', 'SUPP-0008', 'SKU-000023', 24, 48, 12.01, 12, 1.0, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0003-SKU-000023', 'SUPP-0003', 'SKU-000023', 24, 24, 12.61, 14, 1.2, FALSE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0006-SKU-000024', 'SUPP-0006', 'SKU-000024', 24, 96, 9.4, 6, 1.5, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0001-SKU-000025', 'SUPP-0001', 'SKU-000025', 6, 6, 5.43, 3, 0.9, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0010-SKU-000026', 'SUPP-0010', 'SKU-000026', 24, 96, 4.75, 3, 1.2, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0007-SKU-000027', 'SUPP-0007', 'SKU-000027', 12, 60, 2.08, 10, 0.8, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0002-SKU-000028', 'SUPP-0002', 'SKU-000028', 12, 48, 20.55, 6, 1.3, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0009-SKU-000028', 'SUPP-0009', 'SKU-000028', 12, 36, 21.58, 7, 1.6, FALSE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0010-SKU-000029', 'SUPP-0010', 'SKU-000029', 12, 24, 2.87, 4, 1.5, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0007-SKU-000030', 'SUPP-0007', 'SKU-000030', 6, 6, 4.18, 7, 1.4, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0003-SKU-000031', 'SUPP-0003', 'SKU-000031', 6, 24, 2.33, 10, 0.7, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0009-SKU-000031', 'SUPP-0009', 'SKU-000031', 6, 18, 2.45, 12, 0.8, FALSE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0003-SKU-000032', 'SUPP-0003', 'SKU-000032', 24, 96, 2.05, 10, 1.5, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0002-SKU-000033', 'SUPP-0002', 'SKU-000033', 24, 96, 15.69, 4, 2.0, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0003-SKU-000034', 'SUPP-0003', 'SKU-000034', 6, 24, 15.39, 5, 0.7, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0004-SKU-000035', 'SUPP-0004', 'SKU-000035', 24, 24, 0.91, 11, 1.9, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0003-SKU-000036', 'SUPP-0003', 'SKU-000036', 48, 192, 11.52, 7, 1.4, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0006-SKU-000037', 'SUPP-0006', 'SKU-000037', 24, 96, 3.41, 9, 0.9, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0005-SKU-000037', 'SUPP-0005', 'SKU-000037', 24, 72, 3.58, 9, 1.1, FALSE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0010-SKU-000038', 'SUPP-0010', 'SKU-000038', 6, 24, 4.95, 7, 1.8, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0009-SKU-000039', 'SUPP-0009', 'SKU-000039', 24, 24, 3.33, 3, 0.9, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0008-SKU-000040', 'SUPP-0008', 'SKU-000040', 24, 24, 1.72, 9, 0.8, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0008-SKU-000041', 'SUPP-0008', 'SKU-000041', 48, 96, 23.48, 5, 1.1, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0005-SKU-000042', 'SUPP-0005', 'SKU-000042', 24, 96, 0.83, 4, 1.9, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0010-SKU-000043', 'SUPP-0010', 'SKU-000043', 48, 96, 1.09, 10, 1.0, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0009-SKU-000044', 'SUPP-0009', 'SKU-000044', 12, 12, 1.97, 4, 0.8, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0005-SKU-000045', 'SUPP-0005', 'SKU-000045', 12, 48, 13.6, 7, 1.1, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0003-SKU-000046', 'SUPP-0003', 'SKU-000046', 48, 240, 3.87, 7, 1.4, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0002-SKU-000047', 'SUPP-0002', 'SKU-000047', 24, 48, 4.96, 4, 1.0, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0005-SKU-000048', 'SUPP-0005', 'SKU-000048', 6, 24, 19.7, 12, 1.5, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0002-SKU-000048', 'SUPP-0002', 'SKU-000048', 6, 18, 20.68, 14, 1.8, FALSE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0009-SKU-000049', 'SUPP-0009', 'SKU-000049', 48, 96, 2.34, 11, 0.7, TRUE, '2025-01-01', NULL);
INSERT INTO supplier_skus (supplier_sku_id, supplier_id, sku_id, pack_size, moq_units, unit_purchase_cost, nominal_lead_time_days, lead_time_std_days, is_primary, effective_from, effective_to) VALUES ('SSKU-SUPP-0009-SKU-000050', 'SUPP-0009', 'SKU-000050', 6, 30, 6.65, 11, 1.9, TRUE, '2025-01-01', NULL);

