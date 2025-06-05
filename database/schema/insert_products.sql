-- Insert Sälka/Salka products from the filtered products.csv
-- Using product_sku as the primary key
-- BEGIN/COMMIT ensures one transaction (no partial insertion)
-- Product Data Set for March 2025

BEGIN;

INSERT INTO products (product_id, product_sku, product_name, product_color)
VALUES 
    ('6739053f7dd5b40cf6ecf1ec', 'SQ1399946', 'Sälka Art Sling (made to order)', 'Wild Lupine (Purple)'),
    ('6739053f7dd5b40cf6ecf1ec', 'SQ5375200', 'Sälka Art Sling (made to order)', 'Misty Fern (Green)'),
    ('6739053f7dd5b40cf6ecf1ec', 'SQ7558466', 'Sälka Art Sling (made to order)', 'Honey Pinecone (Brown)'),
    ('6739053f7dd5b40cf6ecf1ec', 'SQ0934585', 'Sälka Art Sling (made to order)', 'Alpine Lake (Teal)'),
    ('6739053f7dd5b40cf6ecf1ec', 'SQ2405814', 'Sälka Art Sling (made to order)', 'Midnight Pine (Black)'),
    ('67e85a0943f0be29d32c5d75', 'SQ9055246', 'Sälka Art Sling - 🌸 Wildflower Edition', 'Paintbrush (Peach/Red)'),
    ('67e85a0943f0be29d32c5d75', 'SQ8266292', 'Sälka Art Sling - 🌸 Wildflower Edition', 'Lupine (Purple/Blue)'),
    ('67e8aa527b8d5927f931a374', 'SQ5747971', 'Sälka Art Sling - 🌸 Wildflower Edition (Seconds)', 'Lupine (Purple/Blue)'),
    ('662714acca61972774d6b0f4', 'SQ8414928', 'Sälka Pencil Pouch (made to order)', 'Sagebrush (Gray-Green)'),
    ('662714acca61972774d6b0f4', 'SQ5627159', 'Sälka Pencil Pouch (made to order)', 'Toasted Cinnamon (Brown)'),
    ('66297d7ab171d427493966f9', 'SQ8838225', 'Sälka Artboard Pouch (made to order)', 'Sagebrush (Gray/Green)'),
    ('66297d7ab171d427493966f9', 'SQ2367717', 'Sälka Artboard Pouch (made to order)', 'Toasted Cinnamon (Brown)'),
    ('66297e170cf57c0a4aa62f83', 'SQ5132857', 'Sälka Explorer Bundle', 'Sagebrush (Gray-Green)'),
    ('66297e170cf57c0a4aa62f83', 'SQ6227203', 'Sälka Explorer Bundle', 'Toasted Cinnamon (Brown)'),
    ('66e1f32114a4dd2ed882672c', 'SQ4897743', 'Sälka Mini Pouch', 'Wild Lupine (Purple)'),
    ('66e1f32114a4dd2ed882672c', 'SQ9842481', 'Sälka Mini Pouch', 'Misty Fern (Green)'),
    ('66e1f32114a4dd2ed882672c', 'SQ4534244', 'Sälka Mini Pouch', 'Honey Pinecone (Brown)'),
    ('66e1f32114a4dd2ed882672c', 'SQ9040450', 'Sälka Mini Pouch', 'Midnight Pine (Black)'),
    ('66e1f32114a4dd2ed882672c', 'SQ9656091', 'Sälka Mini Pouch', 'Alpine Lake (Teal)'),
    ('67d4c2408992f6234197f340', 'SQ1775912', 'Sälka Mini Pouch - 🌸 Wildflower Edition', 'Mesa Glow'),
    ('67d4c2408992f6234197f340', 'SQ9057794', 'Sälka Mini Pouch - 🌸 Wildflower Edition', 'Canyon Blush'),
    ('67d4c2408992f6234197f340', 'SQ0620981', 'Sälka Mini Pouch - 🌸 Wildflower Edition', 'Starlit Sky'),
    ('67d4c2408992f6234197f340', 'SQ4762660', 'Sälka Mini Pouch - 🌸 Wildflower Edition', 'Bluebell');

COMMIT;