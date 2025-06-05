BEGIN;

-- Update using the migration log we created in /update_products.sql
UPDATE bill_of_materials bom
SET 
    product_sku = sml.new_sku,
    modified_at = CURRENT_TIMESTAMP
FROM sku_migration_log sml
WHERE bom.product_sku = sml.old_sku;

COMMIT;