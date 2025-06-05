-- Inserts new order rows and updates existing rows on conflict
-- Expects ETL to add new order table data to temp_orders_staging table
-- Return value of rows_affected is required for jdbc.read functionality in custom code Glue node

CREATE OR REPLACE FUNCTION upsert_orders_from_staging()
RETURNS INTEGER AS $$
DECLARE
    rows_affected INTEGER := 0;
BEGIN
    INSERT INTO orders (
        order_id, order_number, created_on, modified_on, fulfilled_on,
        customer_email, customer_name, shipping_city, shipping_state, 
        shipping_country, fulfillment_status, discount_total, refund_total, order_total
    )
    SELECT 
        order_id, order_number, created_on, modified_on, fulfilled_on,
        customer_email, customer_name, shipping_city, shipping_state, 
        shipping_country, fulfillment_status, discount_total, refund_total, order_total
    FROM temp_orders_staging
    ON CONFLICT (order_id) DO UPDATE SET
        order_number = EXCLUDED.order_number,
        created_on = EXCLUDED.created_on,
        modified_on = EXCLUDED.modified_on,
        fulfilled_on = EXCLUDED.fulfilled_on,
        customer_email = EXCLUDED.customer_email,
        customer_name = EXCLUDED.customer_name,
        shipping_city = EXCLUDED.shipping_city,
        shipping_state = EXCLUDED.shipping_state,
        shipping_country = EXCLUDED.shipping_country,
        fulfillment_status = EXCLUDED.fulfillment_status,
        discount_total = EXCLUDED.discount_total,
        refund_total = EXCLUDED.refund_total,
        order_total = EXCLUDED.order_total;
    
    -- Get the number of rows affected
    GET DIAGNOSTICS rows_affected = ROW_COUNT;
    
    -- Returns number of rows updated (or 0 for none)
    RETURN rows_affected;
END;
-- Native procedural language: required for DECLARE (variable), BEGIN/END, and GET DIAGNOSTICS.
-- Cannot simply return ROW_COUNT. We have to assign it to a variable to access outside of GET DIAGNOSTICS.
$$ LANGUAGE plpgsql;