import json
import os

import boto3


def lambda_handler(event, context):
    try:
        # Get environment variables
        api_id = os.environ.get('API_ID')
        dynamodb_tables = json.loads(os.environ.get('DYNAMODB_TABLES', '[]'))
        environment = os.environ.get('ENVIRONMENT')
        lambda_function_name = os.environ.get('LAMBDA_FUNCTION_NAME')
        
        # Initialize AWS clients
        apigateway = boto3.client('apigateway')
        dynamodb = boto3.client('dynamodb')
        lambda_client = boto3.client('lambda')
        
        # Verify API Gateway
        try:
            api_response = apigateway.get_rest_api(restApiId=api_id)
            print(f"API Gateway verification successful: {api_response['name']}")
        except Exception as e:
            print(f"API Gateway verification failed: {str(e)}")
            raise
        
        # Verify DynamoDB tables
        for table_name in dynamodb_tables:
            try:
                table_response = dynamodb.describe_table(TableName=table_name)
                print(f"DynamoDB table verification successful: {table_name}")
            except Exception as e:
                print(f"DynamoDB table verification failed for {table_name}: {str(e)}")
                raise
        
        # Verify Lambda function
        try:
            lambda_response = lambda_client.get_function(FunctionName=lambda_function_name)
            print(f"Lambda function verification successful: {lambda_function_name}")
        except Exception as e:
            print(f"Lambda function verification failed: {str(e)}")
            raise
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Deployment verification successful',
                'environment': environment,
                'verified_resources': {
                    'api_gateway': api_id,
                    'dynamodb_tables': dynamodb_tables,
                    'lambda_function': lambda_function_name
                }
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Deployment verification failed',
                'error': str(e)
            })
        } 