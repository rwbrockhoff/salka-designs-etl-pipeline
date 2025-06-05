# Sälka Designs ETL Pipeline - Lambda Functions

## Functions Overview

### 1. `getSalkaOrders` - Data Ingestion

**Trigger:** EventBridge Scheduler (Monday 5am MST)  
**Purpose:** Extract order data from Squarespace API and initiate processing

**Key Features:**

- Retrieves API credentials from AWS Secrets Manager
- Fetches order data from Squarespace API
- Stores raw JSON data in S3 with timestamps
- Triggers AWS Glue ETL job for data processing

### 2. `generateSalkaReports` - Report Generation

**Trigger:** EventBridge (after successful Glue ETL completion)  
**Purpose:** Query processed data and generate Excel reports  
**Layers:** AWSSDKPandas-Python313, *sqlAlchemyLayer, *xlsxwriter-layer, _pg8000-layer  
_\* manually packaged/deployed\*

**Key Features:**

- Connects to PostgreSQL RDS using credentials from Secrets Manager
- Generates three business reports using SQL queries:
  - Pending Orders Summary
  - Order Schedule by Date
  - Materials Cut List
- Creates multi-sheet Excel file using pandas
- Uploads reports to S3 with date-based folder structure

### 3. `sendWeeklyOrderReports` - Email Notification

**Trigger:** S3 Event (when .xlsx file uploaded to /reports/\*)  
**Purpose:** Deliver reports to stakeholders via secure email

**Key Features:**

- Generates presigned URLs for secure file access (72-hour expiration)
- Sends professional HTML-formatted emails via Amazon SES
- Extracts report date from S3 file path for email context

## Pipeline Flow

```
EventBridge → getSalkaOrders → Glue ETL → generateSalkaReports → S3 Bucket → sendWeeklyOrderReports
```
