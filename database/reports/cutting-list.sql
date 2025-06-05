SELECT 
    bom.material_piece,
    bom.material_color,
    SUM(bom.material_quantity * oi.product_quantity) AS total_material_needed,
    p.product_name,
    p.product_color,
    SUM(oi.product_quantity) AS total_products_ordered
FROM orders o

JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p ON oi.product_sku = p.product_sku
JOIN bill_of_materials bom ON p.product_sku = bom.product_sku

WHERE lower(o.fulfillment_status) = 'pending'

GROUP BY bom.material_piece, bom.material_color, p.product_name, p.product_color, p.product_sku

ORDER BY bom.material_piece, bom.material_color;