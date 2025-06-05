SELECT 
    DATE(created_on) AS ordered_on, 
    product_sku, 
    product_name, 
    product_color, 
    SUM(product_quantity) AS quantity
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p ON oi.product_sku = p.product_sku
GROUP BY ordered_on, product_sku, product_name, product_color, product_price
ORDER BY ordered_on, product_price DESC;