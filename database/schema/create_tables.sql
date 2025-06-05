CREATE TABLE orders (
    -- Order IDs
    order_id VARCHAR(50) PRIMARY KEY,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Timestamps
    created_on TIMESTAMP NOT NULL,
    modified_on TIMESTAMP NOT NULL,
    fulfilled_on TIMESTAMP NULL,
    
    -- Customer info
    customer_email VARCHAR(100) NOT NULL,
    customer_name VARCHAR(100) NOT NULL, 
    
    -- Shipping information - collected for demographic reporting
    shipping_city VARCHAR(100),
    shipping_state VARCHAR(50),
    shipping_country VARCHAR(50),
    
    -- Order status
    fulfillment_status VARCHAR(20) NOT NULL,
    
    -- Sales info
    discount_total NUMERIC(10,2) NOT NULL DEFAULT 0.00,
    refund_total NUMERIC(10,2) NOT NULL DEFAULT 0.00,
    order_total NUMERIC(10,2) NOT NULL DEFAULT 0.00
);

CREATE TABLE order_items (
	order_item_id SERIAL PRIMARY KEY,
	
	-- Foreign Key (Orders Table)
	order_id VARCHAR(50) NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
	
	-- Product Info
    product_sku VARCHAR(50) NOT NULL,
    product_id VARCHAR(50) NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    product_quantity SMALLINT NOT NULL DEFAULT 1,
    product_price NUMERIC(10,2) NOT NULL DEFAULT 0.00,
    -- Color sometimes includes lead time for customer
    product_color VARCHAR(255)
);

CREATE TABLE products (
    -- Keys
    product_sku VARCHAR(50) NOT NULL UNIQUE PRIMARY KEY,
    -- Product details
    product_id VARCHAR(50) NOT NULL, -- Same product_id shared for product (but not color variant)
    product_name VARCHAR(255) NOT NULL,
    product_color VARCHAR(255) NOT NULL DEFAULT 'Default Color',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE bill_of_materials (
    -- Keys
    material_id SERIAL PRIMARY KEY,
    product_sku VARCHAR(50) NOT NULL REFERENCES products(product_sku) ON DELETE CASCADE,
    
    -- Material details
    material_piece VARCHAR(255) NOT NULL,
    material_color VARCHAR(50) NOT NULL,
    material_quantity SMALLINT NOT NULL DEFAULT 1,
    is_fabric BOOLEAN NOT NULL DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);