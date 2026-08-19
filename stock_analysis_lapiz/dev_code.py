# Feature: Refactored Lambda handler for Production
import io
import os
import json
import requests
import pandas as pd
import boto3
from datetime import datetime
import consonants as con

# Initialize AWS clients outside handler for container reuse
s3_client = boto3.client("s3")
ssm_client = boto3.client("ssm")
sns_client = boto3.client("sns")

# Environment variables
S3_BUCKET_NAME = os.environ.get('OUTPUT_BUCKET_NAME', 'mohana22904')


def send_sns_success():
    success_sns_arn = ssm_client.get_parameter(
        Name=con.SUCCESSNOTIFICATIONARN, 
        WithDecryption=True
    )["Parameter"]["Value"]
    
    component_name = con.COMPONENT_NAME
    env = ssm_client.get_parameter(
        Name=con.ENVIRONMENT, 
        WithDecryption=True
    )['Parameter']['Value']
    
    success_msg = con.SUCCESS_MSG
    sns_message = f"{component_name} : {success_msg}"
    print(sns_message, 'text')
    
    succ_response = sns_client.publish(
        TargetArn=success_sns_arn,
        Message=json.dumps({'default': json.dumps(sns_message)}),
        Subject=f"{env} : {component_name}",
        MessageStructure="json"
    )
    return succ_response


def send_error_sns(msg):
    error_sns_arn = ssm_client.get_parameter(
        Name=con.ERRORNOTIFICATIONARN, 
        WithDecryption=True
    )["Parameter"]["Value"]
    
    env = ssm_client.get_parameter(
        Name=con.ENVIRONMENT, 
        WithDecryption=True
    )['Parameter']['Value']
    
    error_message = f"{con.ERROR_MSG} {msg}"
    component_name = con.COMPONENT_NAME
    sns_message = f"{component_name} : {error_message}"
    
    err_response = sns_client.publish(
        TargetArn=error_sns_arn,
        Message=json.dumps({'default': json.dumps(sns_message)}),
        Subject=f"{env} : {component_name}",
        MessageStructure="json"
    )
    return err_response


def lambda_handler(event, context):
    try:
        # Fetch GitHub API URL inside handler for safe error handling
        github_api_url = ssm_client.get_parameter(
            Name=con.urlapi, 
            WithDecryption=True
        )["Parameter"]["Value"]

        # Dynamic output key format: MM-DD-YYYY/stock_data_HH:MM:SS.csv
        current_time = datetime.now()
        folder_date = current_time.strftime("%m-%d-%Y")
        file_time = current_time.strftime("%H:%M:%S")
        s3_key = f"{folder_date}/stock_data_{file_time}.csv"

        # 1. Fetch directory listing from GitHub API
        headers = {'User-Agent': 'AWS-Lambda-Python'}
        response = requests.get(github_api_url, headers=headers, timeout=10)
        response.raise_for_status()

        files = response.json()
        csv_files = [file['download_url'] for file in files if file['name'].endswith('.csv')]

        if not csv_files:
            return {
                'statusCode': 404,
                'body': json.dumps('No CSV files found in the specified repository path.')
            }

        # 2. Extract metadata CSV (last element)
        meta_csv_url = csv_files.pop()
        meta_df = pd.read_csv(meta_csv_url)

        # 3. Read and combine stock dataframes
        dataframes = []
        for url in csv_files:
            file_name = url.split("/")[-1].replace(".csv", "")
            df = pd.read_csv(url)
            df['Symbol'] = file_name
            dataframes.append(df)

        combined_df = pd.concat(dataframes, ignore_index=True)

        # 4. Merge stock data with metadata
        merged_df = pd.merge(combined_df, meta_df, on='Symbol', how='left')

        # 5. Filter by timestamp range
        merged_df['timestamp'] = pd.to_datetime(merged_df['timestamp'])
        filtered_df = merged_df[
            (merged_df['timestamp'] >= '2021-01-01') & 
            (merged_df['timestamp'] <= '2021-05-26')
        ]

        # 6. Aggregate metrics by Sector
        result_time = filtered_df.groupby("Sector").agg({
            'open': 'mean',
            'close': 'mean',
            'high': 'max',
            'low': 'min',
            'volume': 'mean'
        }).reset_index()

        # 7. Filter specifically for TECHNOLOGY and FINANCE sectors
        list_sector = ["TECHNOLOGY", "FINANCE"]
        result_filtered = result_time[result_time["Sector"].isin(list_sector)].reset_index(drop=True)

        # 8. Rename columns
        result_filtered.columns = [
            'Sector',
            'sector_open_mean',
            'sector_close_mean',
            'sector_high',
            'sector_low',
            'sector_volume_mean'
        ]

        # 9. Write CSV directly to S3
        csv_buffer = io.StringIO()
        result_filtered.to_csv(csv_buffer, index=False, header=True)

        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Body=csv_buffer.getvalue(),
            ContentType='text/csv'
        )

        print("Sending the mail notification")
        send_sns_success()

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Data has been written successfully to S3',
                'bucket': S3_BUCKET_NAME,
                'key': s3_key
            })
        }

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        # Trigger failure notification email/SMS via SNS
        send_error_sns(str(e))
        
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }