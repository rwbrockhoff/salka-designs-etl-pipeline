-- Product migration: Preserve historical data while updating to new e-commerce `product_sku` and `product_id`
-- Strategy: Mark old products as V1, insert new product versions

BEGIN;

-- Update existing products to mark them as legacy versions
UPDATE products 
SET 
    product_name = product_name || ' - V1',
    modified_at = CURRENT_TIMESTAMP
WHERE product_sku IN (
    'SQ1399946', 'SQ5375200', 'SQ7558466', 'SQ0934585', 'SQ2405814',
    'SQ9055246', 'SQ8266292', 'SQ5747971', 'SQ8414928', 'SQ5627159',
    'SQ8838225', 'SQ2367717', 'SQ5132857', 'SQ6227203', 'SQ4897743',
    'SQ9842481', 'SQ4534244', 'SQ9040450', 'SQ9656091', 'SQ1775912',
    'SQ9057794', 'SQ0620981', 'SQ4762660'
);

-- Insert new products with updated SKUs and IDs
INSERT INTO products (product_id, product_sku, product_name, product_color)
VALUES 
    ('6808036c36ea51214f4618a6', 'SQ9731330', 'Sälka Art Sling (made to order)', 'Honey Pinecone (Brown)'),
    ('6808036c36ea51214f4618a6', 'SQ0868125', 'Sälka Art Sling (made to order)', 'Wild Lupine (Purple)'),
    ('6808036c36ea51214f4618a6', 'SQ0934585', 'Sälka Art Sling (made to order)', 'Alpine Lake (Teal)'),
    ('6808036c36ea51214f4618a6', 'SQ0107998', 'Sälka Art Sling (made to order)', 'Misty Fern (Green)'),
    ('6808036c36ea51214f4618a6', 'SQ1103253', 'Sälka Art Sling (made to order)', 'Midnight Pine (Black)'),
    ('68080b7c7869c808d473b6fe', 'SQ0474541', 'Sälka Art Sling - 🌸 Wildflower Edition', 'Lupine (Purple/Blue)'),
    ('68080b7c7869c808d473b6fe', 'SQ7852287', 'Sälka Art Sling - 🌸 Wildflower Edition', 'Paintbrush (Red/Peach)'),
    ('680c205c6384346a0791923c', 'SQ2263500', 'Custom Sälka Sling', 'Paintbrush (Red/Peach)'),
    ('6807f2df7869c808d4739537', 'SQ7220360', 'Sälka Artboard Pouch (made to order)', 'Sagebrush (Gray/Green)'),
    ('6807f2df7869c808d4739537', 'SQ0560910', 'Sälka Artboard Pouch (made to order)', 'Toasted Cinnamon (Brown)'),
    ('6807f48e7869c808d4739769', 'SQ8999124', 'Sälka Explorer Bundle (made to order)', 'Sagebrush (Gray/Green)'),
    ('6807f48e7869c808d4739769', 'SQ7315822', 'Sälka Explorer Bundle (made to order)', 'Toasted Cinnamon (Brown)'),
    ('68080167aa04043fdb21ca3e', 'SQ4990472', 'Sälka Mini Pouch (made to order)', 'Wild Lupine (Purple)'),
    ('68080167aa04043fdb21ca3e', 'SQ2062380', 'Sälka Mini Pouch (made to order)', 'Misty Fern (Green)'),
    ('68080167aa04043fdb21ca3e', 'SQ9213609', 'Sälka Mini Pouch (made to order)', 'Honey Pinecone (Brown)'),
    ('68080167aa04043fdb21ca3e', 'SQ8450711', 'Sälka Mini Pouch (made to order)', 'Alpine Lake (Teal)'),
    ('68080167aa04043fdb21ca3e', 'SQ4226941', 'Sälka Mini Pouch (made to order)', 'Midnight Pine (Black)'),
    ('680809617869c808d473b3f6', 'SQ1135337', 'Sälka Mini Pouch - 🌸 Wildflower Edition', 'Mesa Glow'),
    ('680809617869c808d473b3f6', 'SQ3731643', 'Sälka Mini Pouch - 🌸 Wildflower Edition', 'Canyon Blush'),
    ('680809617869c808d473b3f6', 'SQ4657310', 'Sälka Mini Pouch - 🌸 Wildflower Edition', 'Starlit Sky'),
    ('680809617869c808d473b3f6', 'SQ3876749', 'Sälka Mini Pouch - 🌸 Wildflower Edition', 'Bluebell'),
    ('6807ee747869c808d4738ec4', 'SQ3829705', 'Sälka Pencil Pouch (made to order)', 'Sagebrush (Gray/Green)'),
    ('6807ee747869c808d4738ec4', 'SQ8986626', 'Sälka Pencil Pouch (made to order)', 'Toasted Cinnamon (Brown)');

-- Create mapping table for SKU transitions
CREATE TABLE IF NOT EXISTS sku_migration_log (
    migration_id SERIAL PRIMARY KEY,
    old_sku VARCHAR(50),
    new_sku VARCHAR(50),
    migration_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    migration_reason VARCHAR(255) DEFAULT 'E-commerce migration'
);

-- Log the SKU migrations
INSERT INTO sku_migration_log (old_sku, new_sku, migration_reason)
VALUES 
    ('SQ1399946', 'SQ0868125', 'E-commerce migration - Wild Lupine Art Sling'),
    ('SQ7558466', 'SQ9731330', 'E-commerce migration - Honey Pinecone Art Sling'),
    ('SQ0934585', 'SQ0934585', 'E-commerce migration - Alpine Lake Art Sling (SKU unchanged)'),
    ('SQ5375200', 'SQ0107998', 'E-commerce migration - Misty Fern Art Sling'),
    ('SQ2405814', 'SQ1103253', 'E-commerce migration - Midnight Pine Art Sling');

-- Validate results
-- Expected: 23 legacy products, 23 new products, 5 migration log entries

SELECT 'Legacy products' as category, COUNT(*) as count 
FROM products 
WHERE product_name LIKE '% - V1';

SELECT 'New products' as category, COUNT(*) as count 
FROM products 
WHERE product_name NOT LIKE '% - V1';

SELECT COUNT(*) as migration_entries 
FROM sku_migration_log;

-- ROLLBACK; <-- Used to ensure results match up before committing changes to database
COMMIT; -- <-- Results were as expected, so we updated the DB