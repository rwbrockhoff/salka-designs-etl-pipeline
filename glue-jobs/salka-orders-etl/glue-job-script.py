import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrameCollection
from awsgluedq.transforms import EvaluateDataQuality
from awsglue.dynamicframe import DynamicFrame
from awsglue import DynamicFrame
from pyspark.sql import functions as SqlFuncs


# Script generated for node Save Orders to RDS
def SaveOrdersToRDSTransform(glueContext, dfc) -> DynamicFrameCollection:
    from awsglue.dynamicframe import DynamicFrame, DynamicFrameCollection
    from awsglue.utils import getResolvedOptions
    from pyspark.sql.functions import col
    from pyspark.sql.types import TimestampType
    import boto3
    from botocore.exceptions import ClientError
    from datetime import datetime
    import json
    import sys
    import traceback

    # Job Parmaeters
    try:
        args = getResolvedOptions(
            sys.argv,
            [
                "RDS_SECRET_NAME",
                "AWS_REGION",
                "STAGING_ORDERS_TABLE",
                "ORDER_ITEMS_TABLE",
            ],
        )
        RDS_SECRET_NAME = args["RDS_SECRET_NAME"]
        AWS_REGION = args["AWS_REGION"]
        STAGING_ORDERS_TABLE = args["STAGING_ORDERS_TABLE"]
        ORDER_ITEMS_TABLE = args["ORDER_ITEMS_TABLE"]
    except:
        # Fallback values for data preview
        RDS_SECRET_NAME = "salka-rds-credentials"
        AWS_REGION = "us-east-1"
        STAGING_ORDERS_TABLE = "temp_orders_staging"
        ORDER_ITEMS_TABLE = "order_items"
        print("### Using fallback values for preview mode ###")

    print("### ORDERS TRANSFORM - Upsert Orders ###")

    # Get the DynamicFrame from the collection
    keys = list(dfc.keys())
    df = dfc.select(keys[0])
    dataframe = df.toDF()
    input_df = dataframe

    # Get Spark session
    spark = glueContext.spark_session

    # Define helper functions
    def get_max_date_from_database():
        # Join order_items with orders to get the created_on timestamp
        max_date_query = f"""
            SELECT COALESCE(MAX(o.created_on), '1900-01-01'::timestamp) as max_date 
            FROM {ORDER_ITEMS_TABLE} oi 
            JOIN orders o ON oi.order_id = o.order_id
        """

        result_df = (
            spark.read.format("jdbc")
            .option("url", jdbc_url)
            .option("user", username)
            .option("password", password)
            .option("driver", "org.postgresql.Driver")
            .option("query", max_date_query)
            .load()
        )

        return result_df.collect()[0]["max_date"]

    def get_database_secrets():
        try:
            client = boto3.client("secretsmanager", region_name=AWS_REGION)
            response = client.get_secret_value(SecretId=RDS_SECRET_NAME)
            print(f"### Successfully retrieved credentials for database ###")
            return json.loads(response["SecretString"])

        except ClientError as e:
            statement = "Failed to retrieve database credentials from Secrets Manager"
            raise Exception(f"ERROR: {statement} : {e}")

    # Database connection
    db_credentials = get_database_secrets()
    jdbc_url = f"jdbc:postgresql://{db_credentials['host']}:{db_credentials['port']}/{db_credentials['dbName']}"
    username = db_credentials["username"]
    password = db_credentials["password"]

    jdbc_properties = {
        "user": username,
        "password": password,
        "driver": "org.postgresql.Driver",
    }

    # Select required orders columns
    orders_df = dataframe.select(
        "order_id",
        "order_number",
        "created_on",
        "modified_on",
        "fulfilled_on",
        "customer_email",
        "customer_name",
        "shipping_city",
        "shipping_state",
        "shipping_country",
        "fulfillment_status",
        "discount_total",
        "refund_total",
        "order_total",
    )

    # Select required order item columns (include created_on for metadata)
    order_items_df = dataframe.select(
        "order_id",
        "created_on",
        "product_id",
        "product_sku",
        "product_name",
        "product_quantity",
        "product_price",
        "product_color",
    )

    # Ensure timestamps are properly formatted
    orders_df = orders_df.withColumn(
        "created_on", col("created_on").cast(TimestampType())
    )
    orders_df = orders_df.withColumn(
        "modified_on", col("modified_on").cast(TimestampType())
    )
    orders_df = orders_df.withColumn(
        "fulfilled_on", col("fulfilled_on").cast(TimestampType())
    )
    order_items_df = order_items_df.withColumn(
        "created_on", col("created_on").cast(TimestampType())
    )

    try:
        # 1 - Remove duplicate rows, keeping most recently modified
        staging_orders_df = orders_df.orderBy(col("modified_on").desc()).dropDuplicates(
            ["order_id"]
        )

        # 2 - Write incoming orders to staging table
        print(f"### Writing {staging_orders_df.count()} rows to staging table ###")

        staging_orders_df.write.jdbc(
            url=jdbc_url,
            table=STAGING_ORDERS_TABLE,
            mode="overwrite",
            properties=jdbc_properties,
        )

        print("### Successfully wrote data to staging table ###")

        # 3 - Run stored procedure, returning rows modified
        print("### Executing stored procedure ###")

        result_df = (
            spark.read.format("jdbc")
            .option("url", jdbc_url)
            .option("user", username)
            .option("password", password)
            .option("driver", "org.postgresql.Driver")
            .option("query", "SELECT upsert_orders_from_staging() as rows_modified")
            .load()
        )

        # 4 - Print result to logs
        rows_modified = result_df.collect()[0]["rows_modified"]

        print(f"### Successfully processed {rows_modified} rows ###")
        print("### ORDERS TRANSFORM - Completed successfully ###")

    except Exception as e:
        print(f"### ERROR in ORDERS TRANSFORM: {str(e)} ###")
        print("### Full traceback: ###")
        print(traceback.format_exc())

        # Re-raise exception to fail job if needed
        raise e

    try:
        print(f"### Saving Order Items ###")
        # Only add new order_item rows
        last_processed_timestamp = get_max_date_from_database()
        new_order_items_df = order_items_df.filter(
            col("created_on") > last_processed_timestamp
        )

        print(f"### Total order items: {order_items_df.count()} ###")
        print(f"### New order items to insert: {new_order_items_df.count()} ###")

        # 3 - Insert new items
        if new_order_items_df.count() > 0:

            # Drop created_on column
            final_items_df = new_order_items_df.drop("created_on")

            final_items_df.write.jdbc(
                url=jdbc_url,
                table=ORDER_ITEMS_TABLE,
                mode="append",
                properties=jdbc_properties,
            )

            print(
                f"### Successfully inserted {new_order_items_df.count()} order items ###"
            )
        else:
            # No new order items to save
            print("### No new order items to insert ###")

    except Exception as e:
        print(f"### ERROR in ORDER ITEMS TRANSFORM: {str(e)} ###")
        print("### Full traceback: ###")
        print(traceback.format_exc())

        # Re-raise the exception to fail the job if needed
        raise e

    # Create output dynamic frame
    output_dynamic_frame = DynamicFrame.fromDF(input_df, glueContext, "output")

    # Return as a collection with a single frame (to match expected return type)
    return DynamicFrameCollection({"output_frame": output_dynamic_frame}, glueContext)


def sparkSqlQuery(glueContext, query, mapping, transformation_ctx) -> DynamicFrame:
    for alias, frame in mapping.items():
        frame.toDF().createOrReplaceTempView(alias)
    result = spark.sql(query)
    return DynamicFrame.fromDF(result, glueContext, transformation_ctx)


# Script generated for node Move Processed JSON Files
def MoveProcessedFiles(glueContext, dfc) -> DynamicFrameCollection:
    from awsglue.dynamicframe import DynamicFrameCollection
    from awsglue.utils import getResolvedOptions
    import boto3
    from datetime import datetime
    import sys

    print("### MOVE FILES TRANSFORM - Starting file move operation ###")

    # Job Parameters
    try:
        args = getResolvedOptions(
            sys.argv, ["S3_BUCKET", "RAW_ORDER_FOLDER", "PROCESSED_ORDER_FOLDER"]
        )
        S3_BUCKET = args["S3_BUCKET"]
        RAW_ORDER_FOLDER = args["RAW_ORDER_FOLDER"]
        PROCESSED_ORDER_FOLDER = args["PROCESSED_ORDER_FOLDER"]
    except:
        # Fallback values for preview mode
        S3_BUCKET = "salka-designs"
        RAW_ORDER_FOLDER = "orders/raw/"
        PROCESSED_ORDER_FOLDER = "orders/processed/"

    # Create S3 client
    s3 = boto3.client("s3")

    # Get list of files in raw folder
    response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=RAW_ORDER_FOLDER)

    if "Contents" in response:
        # Get current date for folder structure
        now = datetime.now()
        year = now.strftime("%Y")
        month = now.strftime("%m")
        day = now.strftime("%d")

        # Create processed folder path with date hierarchy
        processed_prefix = f"{PROCESSED_ORDER_FOLDER}{year}/{month}/{day}/"

        # Move each file to processed folder
        for obj in response["Contents"]:
            source_key = obj["Key"]

            # Skip folders, only process files
            if not source_key.endswith("/") and source_key != RAW_ORDER_FOLDER:
                # Extract just the filename
                filename = source_key.split("/")[-1]

                # Create new key with date hierarchy
                target_key = f"{processed_prefix}{filename}"

                print(f"Moving {source_key} to {target_key}")

                # Copy to new location
                s3.copy_object(
                    Bucket=S3_BUCKET,
                    Key=target_key,
                    CopySource={"Bucket": S3_BUCKET, "Key": source_key},
                )

                # Delete from original location
                s3.delete_object(Bucket=S3_BUCKET, Key=source_key)

    print("### MOVE FILES TRANSFORM - Completed successfully ###")

    # Pass through the input data unchanged
    keys = list(dfc.keys())
    output_frame = dfc.select(keys[0])

    return output_frame


args = getResolvedOptions(sys.argv, ["JOB_NAME"])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

# Script generated for node S3 - Sälka Designs Bucket
S3SlkaDesignsBucket_node1746319528121 = glueContext.create_dynamic_frame.from_options(
    format_options={"multiLine": "false"},
    connection_type="s3",
    format="json",
    connection_options={"paths": ["s3://salka-designs/orders/raw/"], "recurse": True},
    transformation_ctx="S3SlkaDesignsBucket_node1746319528121",
)

# Script generated for node RDS SQL Connector
RDSSQLConnector_node1747868232157 = glueContext.create_dynamic_frame.from_options(
    connection_type="postgresql",
    connection_options={
        "useConnectionProperties": "true",
        "dbtable": "glue_connection_dummy",
        "connectionName": "salka-glue-postgres-connection",
    },
    transformation_ctx="RDSSQLConnector_node1747868232157",
)

# Script generated for node Explode & Flatten JSON Data
SqlQuery0 = """
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
    
    -- Shipping address fields
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
    COALESCE(lineItem.variantOptions[0].value, 'Default') as product_color

FROM order_data

LATERAL VIEW explode(result) exploded_orders AS order
LATERAL VIEW explode(order.lineItems) exploded_items AS lineItem
"""
ExplodeFlattenJSONData_node1748030681240 = sparkSqlQuery(
    glueContext,
    query=SqlQuery0,
    mapping={"order_data": S3SlkaDesignsBucket_node1746319528121},
    transformation_ctx="ExplodeFlattenJSONData_node1748030681240",
)

# Script generated for node Data Quality Checks
DataQualityChecks_node1747796831025_ruleset = """
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

DataQualityChecks_node1747796831025 = EvaluateDataQuality().process_rows(
    frame=ExplodeFlattenJSONData_node1748030681240,
    ruleset=DataQualityChecks_node1747796831025_ruleset,
    publishing_options={
        "dataQualityEvaluationContext": "DataQualityChecks_node1747796831025",
        "enableDataQualityCloudWatchMetrics": True,
        "enableDataQualityResultsPublishing": True,
    },
    additional_options={
        "observations.scope": "ALL",
        "performanceTuning.caching": "CACHE_NOTHING",
    },
)

assert (
    DataQualityChecks_node1747796831025[
        EvaluateDataQuality.DATA_QUALITY_RULE_OUTCOMES_KEY
    ]
    .filter(lambda x: x["Outcome"] == "Failed")
    .count()
    == 0
), "The job failed due to failing DQ rules for node: ExplodeFlattenJSONData_node1748030681240"

# Script generated for node originalData
originalData_node1747797982691 = SelectFromCollection.apply(
    dfc=DataQualityChecks_node1747796831025,
    key="originalData",
    transformation_ctx="originalData_node1747797982691",
)

# Script generated for node Drop Duplicates
DropDuplicates_node1747798440191 = DynamicFrame.fromDF(
    originalData_node1747797982691.toDF().dropDuplicates(),
    glueContext,
    "DropDuplicates_node1747798440191",
)

# Script generated for node Save Orders to RDS
SaveOrderstoRDS_node1746801798525 = SaveOrdersToRDSTransform(
    glueContext,
    DynamicFrameCollection(
        {"DropDuplicates_node1747798440191": DropDuplicates_node1747798440191},
        glueContext,
    ),
)

# Script generated for node Move Processed JSON Files
MoveProcessedJSONFiles_node1747698340978 = MoveProcessedFiles(
    glueContext,
    DynamicFrameCollection(
        {"SaveOrderstoRDS_node1746801798525": SaveOrderstoRDS_node1746801798525},
        glueContext,
    ),
)

job.commit()
