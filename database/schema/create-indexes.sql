-- orders indexes
CREATE INDEX idx_orders_created_on ON orders(created_on);           -- For date filtering and sorting
CREATE INDEX idx_orders_fulfillment_status ON orders(fulfillment_status);  -- For status filtering
CREATE INDEX idx_orders_combined_date_status ON orders(created_on, fulfillment_status);  -- For combined filtering

-- order_item indexes
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_product_sku ON order_items(product_sku);

-- products index
CREATE INDEX idx_products_product_sku ON products(product_sku);

-- bill_of_materials index
CREATE INDEX idx_bill_of_materials_product_sku ON bill_of_materials(product_sku);