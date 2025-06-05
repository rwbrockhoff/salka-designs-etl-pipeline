# Data Migration

During this ETL project, the e-commerce business was moved to a separate Squarespace website with a
new API key, new `product_sku`, and new `product_id`. However, we already had exisiting orders in
the database referencing the previous product SKU and id. Production was complete for these orders
and the `bill_of_materials` wouldn't be needed for any further reports or analysis.

### Data Migration Tasks

- Update `bill_of_materials` to use new product skus.
- Update exisiting product name in `products` to append '- V1' so we can easily understand product
  versioning
- Insert new `products` into the database for referential integrity for new orders after e-commerce
  migration.
- Create migration log to track SKU updates for any future product/business changes
