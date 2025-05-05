import json
import os

import boto3
import requests


def lambda_handler(event, context):
    try:
        # Get environment variables
        api_url = os.environ.get('API_URL')
        dynamodb_tables = json.loads(os.environ.get('DYNAMODB_TABLES', '[]'))
        environment = os.environ.get('ENVIRONMENT')
        lambda_function_name = os.environ.get('LAMBDA_FUNCTION_NAME')
        
        # Initialize AWS clients
        dynamodb = boto3.client('dynamodb')
        lambda_client = boto3.client('lambda')
        
        # Test API endpoint
        try:
            response = requests.get(api_url)
            response.raise_for_status()
            print(f"API endpoint test successful: {api_url}")
        except Exception as e:
            print(f"API endpoint test failed: {str(e)}")
            raise
        
        # Test DynamoDB tables
        for table_name in dynamodb_tables:
            try:
                table_response = dynamodb.describe_table(TableName=table_name)
                print(f"DynamoDB table test successful: {table_name}")
            except Exception as e:
                print(f"DynamoDB table test failed for {table_name}: {str(e)}")
                raise
        
        # Test Lambda function
        try:
            lambda_response = lambda_client.invoke(
                FunctionName=lambda_function_name,
                InvocationType='RequestResponse'
            )
            print(f"Lambda function test successful: {lambda_function_name}")
        except Exception as e:
            print(f"Lambda function test failed: {str(e)}")
            raise
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Smoke test successful',
                'environment': environment,
                'tested_resources': {
                    'api_endpoint': api_url,
                    'dynamodb_tables': dynamodb_tables,
                    'lambda_function': lambda_function_name
                }
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Smoke test failed',
                'error': str(e)
            })
        } 