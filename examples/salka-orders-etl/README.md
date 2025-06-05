# Sälka Designs Example Files

### [Mock .JSON File (Data Ingestion)](/examples/salka-orders-etl/squarespace-api-response/squarespace_orders_04012025_050400-mock-data.json)

**Location:** Squarespace API → AWS S3 Bucket

Mock JSON response from the Squarespace Orders API demonstrating the expected data structure for
this ETL pipeline. This file represents the raw data that gets fetched and stored in AWS S3 before
being processed by our AWS Glue ETL job.

### [Sample Excel Report](/examples/salka-orders-etl/reports/salka_order_reports_2025-04-01.xlsx)

**Location:** AWS S3 Bucket → Client Email via AWS SES

Sample report file (deliverable) that meets the business requirements for this project. Report has
been modified to obscure real-time business order information.
