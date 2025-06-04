import json
import boto3
import os
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from botocore.exceptions import ClientError


def lambda_handler(event, context):
    # Lambda function to send an email with a presigned URL to an Excel report.
    # Triggered by S3 event when a new Excel file is uploaded to the reports folder.

    print("Email notification Lambda triggered")

    try:
        # Get email configuration from env variables
        sender_email = os.environ.get("SENDER_EMAIL")
        recipient_emails_str = os.environ.get("RECIPIENT_EMAILS")

        if not sender_email:
            raise ValueError("Missing required env variable: SENDER_EMAIL")
        if not recipient_emails_str:
            raise ValueError("Missing required env variable: RECIPIENT_EMAILS")

        recipient_emails = recipient_emails_str.split(",")

        # Get S3 bucket folder/file structure
        bucket, key = extract_s3_info(event)
        print(f"Processing file: {bucket}/{key}")

        # Check file type (redundant with S3 trigger)
        if not key.lower().endswith(".xlsx"):
            print(f"File is not an Excel file, skipping: {key}")
            return {"statusCode": 200, "body": "Skipped. No excel files found."}

        # Generate a presigned URL for the file (valid for 48 hours)
        file_url = generate_presigned_url(bucket, key)

        if not file_url:
            raise Exception("Failed to generate presigned URL")

        # Send the email with the report link
        message_id = send_report_email(file_url, key, sender_email, recipient_emails)

        return {
            "statusCode": 200,
            "body": f"Email sent successfully with MessageID: {message_id}",
        }

    except Exception as e:
        print(f"Error processing event: {str(e)}")
        print(f"Event: {json.dumps(event)}")
        raise


def extract_s3_info(event):
    # Extract bucket and key from S3 event
    try:
        s3_record = event["Records"][0]["s3"]
        bucket = s3_record["bucket"]["name"]
        # URL decode the key (S3 events come URL encoded)
        key = s3_record["object"]["key"].replace("%3A", ":").replace("%2F", "/")
        return bucket, key

    except (KeyError, IndexError) as e:
        print(f"Error extracting S3 info from event: {str(e)}")
        raise ValueError(f"Invalid S3 event structure: {e}")


def generate_presigned_url(bucket, key, expiration=259200):
    # Generate a presigned URL for an S3 object
    s3_client = boto3.client("s3")
    try:
        url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expiration,  # URL valid for 72 hours by default
        )
        print(f"Generated presigned URL (expires in {expiration/3600} hours)")
        return url

    except Exception as e:
        print(f"Error generating presigned URL: {str(e)}")
        return None


def send_report_email(file_url, file_key, sender_email, recipient_emails):
    # Send an email with a presigned URL link to the report

    # Extract filename from key
    file_name = file_key.split("/")[-1]

    # Extract date from the file path (assuming format reports/YYYY/MM/DD/filename.xlsx)
    try:
        path_parts = file_key.split("/")
        if len(path_parts) >= 4:  # We have enough path components
            report_date = f"{path_parts[1]}-{path_parts[2]}-{path_parts[3]}"
        else:
            report_date = datetime.now().strftime("%Y-%m-%d")
    except:
        report_date = datetime.now().strftime("%Y-%m-%d")

    # Format the date for display (May 1, 2025)
    try:
        date_obj = datetime.strptime(report_date, "%Y-%m-%d")
        today_formatted = date_obj.strftime("%B %d, %Y")
    except:
        today_formatted = datetime.now().strftime("%B %d, %Y")

    # Create a multipart message
    msg = MIMEMultipart()
    msg["Subject"] = f"Salka Designs Orders Report - {report_date}"
    msg["From"] = sender_email
    msg["To"] = ", ".join(recipient_emails)

    # Email body with HTML formatting and button
    body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px">
                <div style="text-align: center; margin-bottom: 20px">
                    <h2 style="color: #4a6c6f">Salka Designs Order Report</h2>
                    <p style="color: #666">{today_formatted}</p>
                </div>

                <p>Hello team,</p>

                <p>Your latest Salka Designs order report is available.</p>

                <div style="margin: 30px 0; text-align: center">
                    <a
                    href="{file_url}"
                    style="
                        background-color: #4a6c6f;
                        color: white;
                        padding: 12px 20px;
                        text-decoration: none;
                        border-radius: 4px;
                        font-weight: bold;
                    "
                    >Download Report</a
                    >
                </div>

                <p><strong>Report Details:</strong></p>
                <ul>
                    <li>File: {file_name}</li>
                    <li>Generated: {today_formatted}</li>
                    <li>Link expires in 72 hours</li>
                </ul>

                <p>If you have any questions about this report, please contact me.</p>

                <p>Best regards,<br />Ryan Brockhoff | Data Analyst</p>

                <div
                    style="
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #eee;
                    font-size: 12px;
                    color: #666;
                    "
                >
                    <p>This is an automated message. Please do not reply to this email.</p>
                </div>
                </div>
            </body>
        </html>
    """

    # Attach the HTML body
    msg.attach(MIMEText(body, "html"))

    # Create SES client and send (using default AWS region from Lambda environment)
    ses_client = boto3.client("ses")

    try:
        response = ses_client.send_raw_email(
            Source=sender_email,
            Destinations=recipient_emails,
            RawMessage={"Data": msg.as_string()},
        )
        message_id = response["MessageId"]
        print(f"Email with report link sent! Message ID: {message_id}")
        return message_id
    except ClientError as e:
        print(f"Error sending email: {e.response['Error']['Message']}")
        raise e
