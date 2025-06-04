import boto3
import pandas as pd
import json
import os
from datetime import datetime
from sqlalchemy import create_engine, text
from botocore.exceptions import ClientError

print("Starting Salka pending orders reports job")


# Get database credentials
def get_secret():
    secret_name = "salka-rds-credentials"
    region = "us-east-1"
    client = boto3.client("secretsmanager", region_name=region)
    try:
        response = client.get_secret_value(SecretId=secret_name)
        return json.loads(response["SecretString"])
    except ClientError as e:
        raise e


# Connect to RDS
def get_db_connection():
    secret = get_secret()
    conn_string = f"postgresql+pg8000://{secret['username']}:{secret['password']}@{secret['host']}:{secret['port']}/{secret['dbName']}"
    engine = create_engine(conn_string)

    return engine


def generate_df(sql_query, engine, result_name):
    try:
        dataframe = pd.read_sql(text(sql_query), engine)
        print(f"Retrieved {len(dataframe)} rows from {result_name}")
        return dataframe
    except:
        print(f"Failed to generate dataframe for {result_name}")


# Generate and save reports
def generate_reports():
    # Connect to the database
    engine = get_db_connection()

    # Set up S3 client
    s3_client = boto3.client("s3")

    # Get today's date for folder structure
    now = datetime.now()
    formatted_date = now.strftime("%Y-%m-%d")
    year = now.strftime("%Y")
    month = now.strftime("%m")
    day = now.strftime("%d")

    output_bucket = os.environ.get("OUTPUT_BUCKET", "salka-reports")

    try:
        print("Executing SQL queries...")

        # Report 1: Pending Orders Summary
        print("Generating pending orders report...")

        pending_orders_query = """
        SELECT product_sku, product_name, product_color, sum(product_quantity) AS quantity
        FROM orders o
        JOIN order_items oi
        ON o.order_id = oi.order_id
        WHERE lower(fulfillment_status) = 'pending'
        GROUP BY product_sku, product_name, product_color, product_price
        ORDER BY product_price DESC
        """

        pending_orders_df = generate_df(pending_orders_query, engine, "Pending  Orders")

        # Report 2: Orders Schedule by Due Date
        print("Generating order schedule report...")

        schedule_query = """
        SELECT DATE(created_on) as ordered_on, product_sku, product_name, 
            product_color, sum(product_quantity) as quantity
        FROM orders o
        JOIN order_items oi
        ON o.order_id = oi.order_id
        GROUP BY ordered_on, product_sku, product_name, product_color, product_price
        ORDER BY ordered_on, product_price DESC
        """

        schedule_df = generate_df(schedule_query, engine, "Order Schedule")

        # Report 3: Cut List (joining with BOM)
        print("Generating materials cut list...")
        cut_list_query = """
        SELECT 
            bom.material_piece, bom.material_color, 
            SUM(bom.material_quantity * oi.product_quantity) AS total_material_needed,
            p.product_name, p.product_color, SUM(oi.product_quantity) AS total_products_ordered
        FROM 
            orders o
        JOIN 
            order_items oi ON o.order_id = oi.order_id
        JOIN 
            products p ON oi.product_sku = p.product_sku
        JOIN 
            bill_of_materials bom ON p.product_sku = bom.product_sku
        WHERE 
            lower(o.fulfillment_status) = 'pending'
        GROUP BY 
            bom.material_piece, bom.material_color,
            p.product_name, p.product_color, p.product_sku
        ORDER BY 
            bom.material_piece, bom.material_color
        """

        cut_list_df = generate_df(cut_list_query, engine, "Cut List")

        # Create report folder path with date
        report_folder = f"reports/{year}/{month}/{day}"

        # Save to temporary location
        tmp_path = "/tmp"
        pending_orders_path = f"{tmp_path}/pending_orders.csv"
        schedule_path = f"{tmp_path}/order_schedule.csv"
        cut_list_path = f"{tmp_path}/cut_list.csv"
        excel_path = f"{tmp_path}/salka_order_reports.xlsx"

        # Save as CSV files
        print("Creating CSV files...")
        pending_orders_df.to_csv(pending_orders_path, index=False)
        schedule_df.to_csv(schedule_path, index=False)
        cut_list_df.to_csv(cut_list_path, index=False)

        # Create Excel with multiple sheets
        print("Creating Excel report with multiple sheets...")
        with pd.ExcelWriter(excel_path, engine="xlsxwriter") as writer:
            pending_orders_df.to_excel(writer, sheet_name="Pending Orders", index=False)
            schedule_df.to_excel(writer, sheet_name="Order Schedule", index=False)
            cut_list_df.to_excel(writer, sheet_name="Materials Cut List", index=False)

        print(f"Uploading reports to S3 bucket: {output_bucket}/{report_folder}")

        # Upload to S3
        s3_client.upload_file(
            pending_orders_path,
            output_bucket,
            f"{report_folder}/pending_orders_{formatted_date}.csv",
        )
        s3_client.upload_file(
            schedule_path,
            output_bucket,
            f"{report_folder}/order_schedule_{formatted_date}.csv",
        )
        s3_client.upload_file(
            cut_list_path,
            output_bucket,
            f"{report_folder}/cut_list_{formatted_date}.csv",
        )
        s3_client.upload_file(
            excel_path,
            output_bucket,
            f"{report_folder}/salka_order_reports_{formatted_date}.xlsx",
        )

        print("All reports generated and saved to S3 successfully")
        return True

    except Exception as e:
        print(f"Error generating reports: {str(e)}")
        raise


# main lambda execution
def lambda_handler(event, context):
    try:
        # Generate reports
        generate_reports()
        return {"statusCode": 200, "body": "Salka reporting job completed successfully"}

    except Exception as e:
        print(f"Job failed: {str(e)}")
        return {"statusCode": 500, "body": f"Job failed: {str(e)}"}
