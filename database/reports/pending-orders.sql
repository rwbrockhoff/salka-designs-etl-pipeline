SELECT 
    product_sku, 
    product_name, 
    product_color, 
    sum(product_quantity) AS quantity
FROM orders o
JOIN order_items oi
ON o.order_id = oi.order_id
WHERE lower(fulfillment_status) = 'pending'
GROUP BY product_sku, product_name, product_color, product_price
ORDER BY product_price DESC;