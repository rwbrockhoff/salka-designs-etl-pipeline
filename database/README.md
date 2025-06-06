# Database

This folder contains the PostgreSQL database schema, reports, and procedures for the Salka Designs
ETL Pipeline. The database stores Squarespace order data and product information to support weekly
production reporting.

### Database Schema

![Database Schema](/docs/salka-db-schema.png)

### Reports

The `/reports` folder contains SQL queries used by the ETL pipeline to generate weekly Excel
reports:

**pending-orders.sql**

- Lists products with pending fulfillment
- Aggregates quantities by SKU and color
- Sorted by product price (descending)

**order-schedule.sql**

- Daily breakdown of orders by product
- Groups by order date and product details
- Used for production planning

**cutting-list.sql**

- Material requirements for pending orders
- Joins orders → order_items → products → bill_of_materials
- Calculates total fabric needed by material type and color

### Stored Procedures

**upsert_orders_from_staging()**

- Handles ETL data loading from staging table
- Inserts new orders and updates existing ones on conflict
- Returns row count for AWS Glue integration

### Data Migration

During the project, the e-commerce business migrated to a new Squarespace website with new API keys
and product identifiers. The `/data-migration` folder handles this transition:

**update-products.sql**

- Preserves previous product data by appending "- V1" to existing product names
- Inserts new products with updated SKUs and IDs
- Creates `sku_migration_log` table to track changes

**update-bom.sql**

- Updates bill of materials to reference new product SKUs
- Uses the migration log to update SKUs in `bill_of_materials` table
- Maintains referential integrity between new products and material list
