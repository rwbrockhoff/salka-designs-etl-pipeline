import json
import boto3
import requests
import os
from datetime import datetime

# S3 Client
s3_client = boto3.client('s3')

# ENV
SQUARESPACE_ORDER_ENDPOINT = os.environ.get('SQUARESPACE_ORDER_ENDPOINT')
RAW_DATA_BUCKET = os.environ.get('RAW_DATA_BUCKET')
SALKA_GLUE_JOB = os.environ.get('SALKA_GLUE_JOB')
SQUARESPACE_SECRET_NAME = os.environ.get('SQUARESPACE_SECRET_NAME')

def lambda_handler(event, context):
    # Extract order data from Squarespace API and save to S3
    try:
        timestamp = datetime.now().strftime("%m%d%Y_%H%M%S")
        raw_orders_key = f"orders/raw/squarespace_orders_{timestamp}.json"
        
        # Step 1: Get raw orders from Squarespace API
        raw_orders_data = get_squarespace_orders()

        # Step 2: Save raw JSON data to S3
        s3_file_location = save_json_to_s3(raw_orders_data, RAW_DATA_BUCKET, raw_orders_key)
        
        # Step 3: Trigger Glue job to process the raw data
        glue_job_run_id = run_glue_job()
        
        # Return success with metadata
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
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }
    
def get_squarespace_api_key():
    try:
        # Get API key from Secrets Manager
        client = boto3.client('secretsmanager')
        response = client.get_secret_value(SecretId=SQUARESPACE_SECRET_NAME)
        secret = json.loads(response['SecretString'])

        squarespace_api_key = secret['SQUARESPACE_API_KEY']

        if squarespace_api_key:
            return squarespace_api_key
        else:
            raise Exception("No API KEY returned from Secrets Manager")

    except Exception as e:
        print(f"Error retrieving Squarespace API Key: {str(e)}")
        raise Exception(f"Failed to get Squarespace API Key: {str(e)}")

def get_squarespace_orders():
    squarespace_api_key = get_squarespace_api_key()
    headers = {
        'Authorization': f'Bearer {squarespace_api_key}',
        'Content-Type': 'application/json'
    }
    
    response = requests.get(SQUARESPACE_ORDER_ENDPOINT, headers=headers)

    # Return the raw JSON response
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch orders: {response.status_code}, {response.text}")

def save_json_to_s3(json_data, bucket, key):
    try: 
        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(json_data),
            ContentType='application/json'
        )
        
        s3_location = f"s3://{bucket}/{key}"
        print(f"Successfully saved json order data to {s3_location}")
        return s3_location
    
    except Exception as e:
        print(f"Error saving json order data to S3: {str(e)}")
        raise Exception(f"Failed to save json order data to S3: {str(e)}")

def run_glue_job():
    try:
        glue_client = boto3.client('glue')
        response = glue_client.start_job_run(JobName=SALKA_GLUE_JOB)

        print(f"Started Glue job with ID: {response['JobRunId']}")
        return response['JobRunId']
    
    except Exception as e:
        print(f"Error running the glue job: {str(e)}")
        raise Exception(f"Failed to run glue job to process order data: {str(e)}")