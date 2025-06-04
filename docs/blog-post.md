# Sälka Designs: Automated ETL & Analytics Pipeline

Serverless ETL pipeline that automatically ingests Squarespace order data, validates quality, and
delivers weekly production reports via email.

[View Blog Post Here](https://ryanbrockhoff.com/blog/data-analytics/salka-designs-automated-etl/)

**Technologies Used:** AWS Lambda, AWS Glue, Amazon RDS (PostgreSQL), Amazon S3, Amazon EventBridge,
Amazon SES, AWS Secrets Manager, VPC, Python, SQL, Pandas, Squarespace API

---

## 1. Project Overview & Business Context

### Project Summary

Sälka Designs is a small business looking to streamline their production process by automating their
production schedule and bill of materials (often referred to as a BOM). The goal was to create an
automated, cloud-based pipeline that would ingest their order data from their Squarespace e-commerce
and create a report to help the production team with managing weekly orders. In addition, we needed
to store the cleaned data in a database for future sales reports and other extensions from this
project based on business needs.

This will allow the team to save valuable time manually aggregating order information, avoid
fulfillment errors, and gain business insights into their weekly fluctuation of orders to better
manage inventory, production, and work schedules.

### Project Requirements

Sälka Designs needs a weekly excel file with three separate reports:

- **Pending Orders** - Outstanding orders requiring fulfillment
- **Order Schedule** - Timeline for production planning
- **Bill of Materials (BOM)** - Materials cut list for procurement

The data included private customer information and needed to be stored securely.

### Design Considerations

Given the sensitive nature of customer data and the need for reliable weekly reporting, the solution
required:

- **Security**: Strong data protection for customer information
- **Automation**: Automated weekly report generation and delivery
- **Scalability**: Ability to handle growing order volumes without modification
- **Reliability**: Data quality validation to prevent fulfillment errors
- **Flexibility**: Database storage to support future analytics and reporting needs

## 2. Architecture Overview

![Architecture Diagram](/docs/salka-architecture-diagram.png)

Event-driven pipeline with four main steps:

1. **Data Ingestion** - Automated data extraction from Squarespace API
2. **ETL Processing** - Data transformation, quality validation, and storage
3. **Analytics** - Report generation from cleaned data
4. **Reporting** - Automated email delivery to stakeholders

This serverless approach ensures scalability, cost-effectiveness, and minimal maintenance.

## 3. Data Ingestion Layer

The pipeline begins with automated data collection every Monday at 5am MST using Amazon EventBridge
Scheduler, which triggers the `getSalkaOrders` Lambda function.

**Key Features:**

- Retrieves Squarespace API credentials from AWS Secrets Manager
- Stores complete JSON responses in S3 with timestamped filenames
- Automatically triggers ETL processing via Glue job
- Error handling and logging
- Lambda function role is limited to required resources (S3 bucket, starting glue job)

**Automated Workflow:**

```python
def lambda_handler(event, context):
    try:
        timestamp = datetime.now().strftime("%m%d%Y_%H%M%S")
        raw_orders_key = f"orders/raw/squarespace_orders_{timestamp}.json"

        # Step 1: Get raw orders from Squarespace API
        raw_orders_data = get_squarespace_orders()

        # Step 2: Save raw JSON data to S3
        s3_file_location = save_json_to_s3(raw_orders_data, RAW_DATA_BUCKET, raw_orders_key)

        # Step 3: Trigger Glue job to process the raw data
        glue_job_run_id = run_glue_job()

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Raw Squarespace API data saved',
                'timestamp': timestamp,
                'orders_count': len(raw_orders_data.get('result', [])),
                's3_location': s3_file_location,
                'glue_job_run_id' : glue_job_run_id
            })
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
```

## 4. ETL Processing Layer

#### Why AWS Glue for This Pipeline?

I chose AWS Glue after evaluating several AWS options. AWS DataBrew looked promising for data
cleaning, but cannot handle the complex nested JSON structures from Squarespace or load directly
into PostgreSQL. Amazon Athena could query the JSON files, but I'd need additional tools to get the
data into our database. And of course, RedShift is far too expensive and enterprise-ready than what
a small business would need in this case. Glue offered the right balance: it automatically handles
the JSON transformation, connects directly to our PostgreSQL database, and only charges when the job
runs weekly. For a small business pipeline, the serverless approach made the most sense.

The core transformation happens in an AWS Glue visual ETL job that handles nested JSON structures,
forward filling the customer info for additional line items in the order, handling null values in
required fields, etc. While Glue includes a node for exploding data, it was more succinct to explode
the nested data using SparkSQL (and very satisfying to learn how to unnest data using SparkSQL). The
`explode` takes the list and generates a table with a row for each item, while the `lateral view`
keeps the original row data intact. We could even use `lateral outer view` if we expected null
values or empty lists.

Otherwise, the `explode` would simply create a table like:

```
1 - Product Id - AFASDF
2 - Product SKU - 123123
3 - Produt Name - 'Sälka Sling'
```

Note: The line item `variantOption` is a list that we expect to only ever contain one result.
Otherwise, we would explode the array out into`exploded_variant`.

**JSON Flattening & Transformation:**

```sql
SELECT
    -- Order level fields
    order.id as order_id,
    order.orderNumber as order_number,
    order.createdOn as created_on,
    order.modifiedOn as modified_on,
    order.fulfilledOn as fulfilled_on,
    order.customerEmail as customer_email,

    -- Customer name from shipping address
    CONCAT(order.shippingAddress.firstName, ' ', order.shippingAddress.lastName) as customer_name,

    -- Shipping address fields (not keeping exact physical address)
    order.shippingAddress.city as shipping_city,
    order.shippingAddress.state as shipping_state,
    order.shippingAddress.countryCode as shipping_country,

    -- Order status and totals
    order.fulfillmentStatus as fulfillment_status,
    COALESCE(CAST(order.discountTotal.value AS NUMERIC), 0) AS discount_total,
    COALESCE(CAST(order.refundedTotal.value AS NUMERIC), 0) AS refund_total,
    COALESCE(CAST(order.grandTotal.value AS NUMERIC), 0) AS order_total,

    -- Line item fields
    lineItem.productId as product_id,
    lineItem.sku as product_sku,
    lineItem.productName as product_name,
    lineItem.quantity as product_quantity,
    COALESCE(CAST(lineItem.unitPricePaid.value AS NUMERIC), 0) AS product_price,

    -- Get color from variantOptions array (first element)
    -- This value can be null for some products
    COALESCE(lineItem.variantOptions[0].value, 'Default') as product_color

FROM order_data
LATERAL VIEW explode(result) exploded_orders AS order
LATERAL VIEW explode(order.lineItems) exploded_items AS lineItem
```

**Data Quality Check Rules:** These are rules that are expected for every incoming order. If we
cannot meet these requirements for a Glue job run, we need to change the ETL to handle the new
unexpected changes or products.

```python
# Job fails immediately if any data quality rule fails
DataQualityChecks_ruleset = """
    Rules = [
      RowCount > 0,
      Completeness "order_id" = 1.0,
      Completeness "customer_email" = 1.0,
      Completeness "product_quantity" = 1.0,
      Completeness "product_price" = 1.0,
      Completeness "order_total" = 1.0,
      ColumnValues "product_quantity" > 0,
      ColumnValues "product_price" >= 0
    ]
"""
```

**Dual Output Strategy:**

- **PostgreSQL RDS**: Structured data for analytics and reporting
- **S3 Processed Folder**: Archived data with date partitioning (`YYYY/MM/DD`)

## 5. Database Design & Architecture

The database implements a four-table design that models the complete production workflow for
customer orders and required materials.

### **Database Schema**

![Database Schema](/docs/salka-db-schema.png)

### Handling Delta and Limiting Row Processing

Our orders table is expected to reflect order status changes throughout the production process for
columns: `modified_on`, `fulfilled_on`, and `fulfillment_status`. Otherwise, we could use the
Squarespace API parameters to only fetch orders after a certain timestamp. This added some
additional logic where we needed to update existing orders while appending new ones.

To keep the process as clean as possible, I stored the incoming updated orders in a staging table,
where I then invoked a stored procedure `upsert_orders_from_staging()` to upsert our order rows. If
this stored procedure were to fail, I would have the updated orders in a staging table that I could
easily view during the troubleshooting process.

The biggest challenge for this process was handling jdbc in PySpark, which admittedly is new for me.
The stored procedure could be ran with `spark.read` but requires a value to be returned from the
query statement. So the stored procedure was updated to return rows modified. This works with what
jdbc expects while also giving me a result I can print to my logs.

**Glue: Custom Code Node: Writing transformed data to RDS**

```python
# 1 - Remove duplicates, keeping most recently modified
staging_orders_df = orders_df.orderBy(col("modified_on").desc()).dropDuplicates(["order_id"])

# 2 - Write to staging table for upsert processing
staging_orders_df.write.jdbc(
	url=jdbc_url,
	table=STAGING_ORDERS_TABLE,
	mode="overwrite")

# 3 - Run stored procedure and print modified row count
result_df = spark.read.option("query", "SELECT upsert_orders_from_staging() as rows_modified").load()

rows_modified = result_df.collect()[0]['rows_modified']

print(f"Successfully processed {rows_modified} rows")
```

**Stored Procedure to Handle Upsert:** This stored procedure selects the data stored in
`temp_orders_staging` and attempts to insert into our `orders` table:

- It handles conflicts with existing rows by updating with the latest data from
  `temp_orders_staging` (using `EXCLUDED`).
- It initializes a `rows_affected` variable to 0 and returns total number of rows affected using
  `ROW_COUNT`.
- Returns a value to fulfill what `jdbc` expects from a `spark.read` query.
- Leaves data in `temp_order_staging` until it's overwritten by the next pipeline run (easier
  troubleshooting).

```sql
CREATE OR REPLACE FUNCTION upsert_orders_from_staging()
RETURNS INTEGER AS $$
DECLARE
    rows_affected INTEGER := 0;
BEGIN
    INSERT INTO orders (
		order_id, order_number, created_on, modified_on, fulfilled_on,
		customer_email, customer_name, shipping_city, shipping_state, 
		shipping_country, fulfillment_status, discount_total,
		refund_total, order_total
    )
    SELECT 
		order_id, order_number, created_on, modified_on, fulfilled_on,
		customer_email, customer_name, shipping_city, shipping_state, 
		shipping_country, fulfillment_status, discount_total,
		refund_total, order_total

    FROM temp_orders_staging
   
    ON CONFLICT (order_id) DO UPDATE SET
	    -- Excluded keyword refers to conflicting row values
        order_number = EXCLUDED.order_number,
        created_on = EXCLUDED.created_on,
        modified_on = EXCLUDED.modified_on,
        fulfilled_on = EXCLUDED.fulfilled_on,
        customer_email = EXCLUDED.customer_email,
        customer_name = EXCLUDED.customer_name,
        shipping_city = EXCLUDED.shipping_city,
        shipping_state = EXCLUDED.shipping_state,
        shipping_country = EXCLUDED.shipping_country,
        fulfillment_status = EXCLUDED.fulfillment_status,
        discount_total = EXCLUDED.discount_total,
        refund_total = EXCLUDED.refund_total,
        order_total = EXCLUDED.order_total;

    -- Get the number of rows affected
    -- This is not incremental, but rather a final row count
    -- assigned after insertion from built in ROW_COUNT
    GET DIAGNOSTICS rows_affected = ROW_COUNT;
   
    -- Return the number of rows affected (0 returned if none)
    RETURN rows_affected;
END;

$$ LANGUAGE plpgsql;
```

**Order Items Processing (Incremental Insert):** The `order_items` table is easier to process but
includes significantly more rows (many to one relationship with our `orders` table). To reduce total
items processed here, I use **timestamp-based increment processing**: finding the max or most recent
`created_on` date and only appending new order items to the `order_items` table.

I also debated using a AWS Systems Manager Parameter Store for the timestamp of the last processed
order item. It's a good use case (and would be free to use for a simple variable). However, we don't
use this timestamp anywhere else in our logic and the timestamp is always accessible with a quick
query to RDS.

```python
def get_max_date_from_database():
    # Get the latest order creation date to avoid duplicate order items
    max_date_query = f"""
        SELECT COALESCE(MAX(o.created_on), '1900-01-01'::timestamp) as max_date
        FROM {ORDER_ITEMS_TABLE} oi
        JOIN orders o ON oi.order_id = o.order_id
    """
    return spark.read.option("query", max_date_query).load().collect()[0]['max_date']

# Only process order items newer than last successful run
last_processed_timestamp = get_max_date_from_database()
new_order_items_df = order_items_df.filter(col("created_on") > last_processed_timestamp)

if new_order_items_df.count() > 0:
    final_items_df = new_order_items_df.drop("created_on")
    final_items_df.write.jdbc(url=jdbc_url, table=ORDER_ITEMS_TABLE, mode="append")
    print(f"Successfully inserted {new_order_items_df.count()} order items")
```

**Performance-Optimized Indexing:** I included indexes to help improve query performance for columns
frequently used in `WHERE` clauses, `ORDER BY`, and `JOINS`. Including a composite index for
`created_on` and `fulfillment_status` which are often used in conjunction.

```sql
-- Orders and Order Items indexes
CREATE INDEX idx_orders_created_on ON orders(created_on);
CREATE INDEX idx_orders_fulfillment_status ON orders(fulfillment_status);
-- Composite index for frequently combined columns
CREATE INDEX idx_orders_combined_date_status ON orders(created_on, fulfillment_status);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_product_sku ON order_items(product_sku);
```

#### ETL Features:

- **Inserting Orders Strategy**: Orders use upsert (handle order status changes), order items use
  incremental insert (avoid duplicates)
- **Timestamp-Based Incremental Processing**: Only processes new order items since last successful
  run
- **Handle Duplicates**: Keeps most recently modified order when duplicates exist
- **Error Handling & Logging**: Try/catch with detailed logging and job failure on errors

## 6. Network Security & VPC Configuration

![VPC Security Diagram](/docs/salka-vpc-diagram.png)

Working with customer data, I wanted to ensure solid security practices in my AWS architecture. This
was definitely a fun challenge for me. I wanted to be intentional with my security practices and
really evaluate what services should be isolated within the VPC, versus what needed public access.
My biggest hurdle was establishing the connection between the Glue job and the RDS instance. While I
added the connection to the Glue job, it wasn't until I created a PostgreSQL node within the job
that it would register the connection. One of the many nuances to working with AWS.

I have not worked with a NAT gateway before, but the VPC endpoints were easy to configure since the
Glue job and RDS required minimal access to outside services (CloudWatch, Glue, Secrest, S3). After
a handful of error logs, I was able to get the job running smoothly with all of the required
endpoints added to run the job successfully.
[You can read about my cost optimization for these endpoints here](#cloud-budget-optimization)

**Network Isolation:**

- **Private Subnets**: RDS database has no public internet access
- **VPC Endpoints**: Direct access to AWS services (S3, Secrets Manager) without internet routing
- **Multi-AZ Setup**: High availability across multiple availability zones

**Multiple Security Layers:**

- **Security Groups**: Database only accepts connections from Glue job, report generation Lambda,
  and my bastion server EC2 instance for local dev access with my .pem key.
- **VPC Endpoints**: S3 and other AWS services accessed privately within the VPC
- **Principle of Least Privilege**: Each service has minimal required permissions.

This approach keeps everything modular and easy to troubleshoot, while ensuring we meet security
requirements for storing customer data. It's cost-effective and easy to manage.

## 7. Analytics & Reporting Layer

An event-driven approach triggers our Lambda to generate our reports by querying our updated RDS
database, creating 3 .csv files and 1 .xlsx file (final deliverable) which includes the three
required reports for Sälka Designs.

**Report Generation Lambda:** When ETL processing completes successfully, EventBridge triggers the
`generateSalkaReports` function in the VPC:

```python
# Full Lambda function in Github Repo
def generate_reports():
    # Connect to the database
    engine = get_db_connection()

    # Report 1: Pending Orders Summary
    pending_orders_query = """
    SELECT product_sku, product_name, product_color, sum(product_quantity) AS quantity
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE lower(fulfillment_status) = 'pending'
    GROUP BY product_sku, product_name, product_color, product_price
    ORDER BY product_price DESC
    """

    # Report 2: Orders Schedule by Due Date
    schedule_query = """
    SELECT DATE(created_on) as ordered_on, product_sku, product_name,
        product_color, sum(product_quantity) as quantity
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY ordered_on, product_sku, product_name, product_color, product_price
    ORDER BY ordered_on, product_price DESC
    """

    # Report 3: Cut List (joining with BOM)
    cut_list_query = """
    SELECT
        bom.material_piece, bom.material_color,
        SUM(bom.material_quantity * oi.product_quantity) AS total_material_needed,
        p.product_name, p.product_color,
        SUM(oi.product_quantity) AS total_products_ordered
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN products p ON oi.product_sku = p.product_sku
    JOIN bill_of_materials bom ON p.product_sku = bom.product_sku
    WHERE lower(o.fulfillment_status) = 'pending'
    GROUP BY bom.material_piece, bom.material_color, p.product_name, p.product_color, p.product_sku
    ORDER BY bom.material_piece, bom.material_color
    """

    # Create Excel file with multiple sheets and upload to S3
    with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
        pending_orders_df.to_excel(writer, sheet_name='Pending Orders', index=False)
        schedule_df.to_excel(writer, sheet_name='Order Schedule', index=False)
        cut_list_df.to_excel(writer, sheet_name='Materials Cut List', index=False)
```

### Automated Email Delivery:

When the Excel report is saved to S3, an S3 event automatically triggers the email delivery via the
`sendWeeklyOrderReports` Lambda function that:

- Extracts bucket and file information from the S3 event
- Generates a secure presigned URL with 72-hour expiration
- Sends a professional HTML-formatted email to the production team

![Email Report Preview](/docs/salka-reports-email-preview.png)

## 8. Results & Business Impact

**Automation Achievements:**

- **Time Savings**: Eliminated 2-4 hour weekly manual process
- **Consistency**: Reduced human error in data extraction and formatting
- **Consistent Reporting**: Reports delivered automatically every Monday morning
- **Scalability**: System handles growing order volume without modification

**Business Value Delivered:**

- **Production Planning**: Automated order schedule improves production efficiency
- **Inventory Management**: Bill of materials enables proactive inventory management
- **Fulfillment Accuracy**: Pending orders report prevents missed shipments
- **Operational Efficiency**: Team can focus on production instead of data processing

**Technical Achievements:**

- **Zero Downtime**: Event-driven architecture
- **Cost Optimization**: Serverless approach scales to zero during inactive periods
- **Maintainability**: Clear separation of concerns enables rapid updates and debugging
- **Security**: Enterprise-grade data protection suitable for sensitive customer information

**Future Enhancements:** The modular architecture supports easy expansion for additional data
sources, advanced analytics, and real-time reporting capabilities as Sälka Designs continues to
grow.

This project demonstrates the complete lifecycle of production data engineering: from identifying
specific business requirements through implementing scalable, secure solutions that delivers
valuable business insights to stakeholders. I have always preferred to work with real world projects
that push me to learn new things to "make things work."

---

### Final Note: Cloud Budget Optimization

One of the larger costs for this cloud project is the VPC endpoints which do not need to be running
24/7. While not currently included in this project, a future optimization will be to create two
Lambda functions for endpoint creation and tear down for the VPC prior to the pipeline running
(scheduled with EventBridge). Currently the endpoints are in a single AZ (AWS Availability Zone) to
be more cost-effective, but we can have Multi-AZ set up that only runs during the brief window
required for reporting.

#### Final VPC Endpoint Cost Savings

**Potential Multi-AZ Costs (24/7)** _For production environments where report delivery cannot have
failures due to single zone availability:_

- Multi-AZ: $58.41/month ($700.92/year)

**Current Costs (24/7):**

- Single AZ: $29.21/month ($350.52/year)

**Automated Lambda Approach (2 hour/week):**

- Multi-AZ: $0.64/month ($7.68/year)
- Single AZ: $0.32/month ($3.84/year)

**Annual Savings:** $343-$693 depending on configuration

Configured using the [AWS Pricing Calculator](https://calculator.aws/) comparing 730 hours vs 8
hours of use for VPC PrivateLink (where endpoints are hidden within the VPC portion of the
calculator).
