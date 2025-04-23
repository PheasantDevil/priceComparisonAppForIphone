#!/usr/bin/env python3
import json
import logging
import os
import time

import boto3
import requests

# ロギングの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_api_key():
    """API GatewayのAPIキーを取得"""
    try:
        apigateway = boto3.client('apigateway')
        
        # APIキーが存在しない場合は作成
        response = apigateway.get_api_keys(includeValues=True)
        if not response['items']:
            logger.info("Creating new API key...")
            response = apigateway.create_api_key(
                name="SmokeTestKey",
                enabled=True,
                generateDistinctId=True
            )
            api_key = response['value']
            
            # 使用計画を作成
            usage_plan = apigateway.create_usage_plan(
                name="SmokeTestPlan",
                description="Plan for smoke tests",
                apiStages=[{
                    'apiId': get_api_id(),
                    'stage': 'prod'
                }]
            )
            
            # APIキーを使用計画に関連付け
            apigateway.create_usage_plan_key(
                usagePlanId=usage_plan['id'],
                keyId=response['id'],
                keyType='API_KEY'
            )
            
            return api_key
            
        return response['items'][0]['value']
    except Exception as e:
        logger.error(f"Error getting API key: {e}")
        return None

def get_api_id():
    """API GatewayのIDを取得"""
    try:
        apigateway = boto3.client('apigateway')
        response = apigateway.get_rest_apis()
        if not response['items']:
            logger.error("No API Gateway found")
            return None
        return response['items'][0]['id']
    except Exception as e:
        logger.error(f"Error getting API ID: {e}")
        return None

def get_api_endpoint():
    """API GatewayのエンドポイントURLを取得"""
    try:
        api_id = get_api_id()
        if not api_id:
            return None
            
        region = os.environ.get('AWS_DEFAULT_REGION', 'ap-northeast-1')
        return f"https://{api_id}.execute-api.{region}.amazonaws.com/prod/prices"
    except Exception as e:
        logger.error(f"Error getting API endpoint: {e}")
        return None

def test_lambda_invocation(lambda_client, function_name):
    """Lambda関数の呼び出しテスト"""
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            Payload=json.dumps({})
        )
        status_code = response['StatusCode']
        logger.info(f"Lambda function {function_name} invocation status: {status_code}")
        return status_code == 200
    except Exception as e:
        logger.error(f"Error testing Lambda function {function_name}: {e}")
        return False

def test_dynamodb_operations(dynamodb_client, table_name):
    """DynamoDBの基本操作テスト"""
    try:
        # テーブルの状態を確認
        response = dynamodb_client.describe_table(TableName=table_name)
        status = response['Table']['TableStatus']
        logger.info(f"DynamoDB table {table_name} status: {status}")

        # サンプルデータのスキャン
        response = dynamodb_client.scan(
            TableName=table_name,
            Limit=1
        )
        logger.info(f"Successfully scanned {table_name}")
        return True
    except Exception as e:
        logger.error(f"Error testing DynamoDB table {table_name}: {e}")
        return False

def test_api_endpoint(api_url, api_key=None):
    """APIエンドポイントのテスト"""
    if not api_url:
        logger.error("API endpoint URL is not available")
        return False

    try:
        headers = {}
        if api_key:
            headers['x-api-key'] = api_key

        response = requests.get(api_url, headers=headers)
        status_code = response.status_code
        logger.info(f"API endpoint {api_url} status: {status_code}")
        
        if status_code == 403:
            logger.error("Access denied. Please check API Gateway authentication settings.")
            return False
            
        return status_code == 200
    except requests.exceptions.RequestException as e:
        logger.error(f"Error testing API endpoint {api_url}: {e}")
        return False

def main():
    """メイン関数"""
    try:
        # AWSクライアントの初期化
        lambda_client = boto3.client('lambda')
        dynamodb_client = boto3.client('dynamodb')

        # テスト対象のリソース
        lambda_function = 'get_prices'
        dynamodb_tables = ['iphone_prices', 'official_prices']
        api_url = get_api_endpoint()
        api_key = get_api_key()

        # Lambda関数のテスト
        lambda_result = test_lambda_invocation(lambda_client, lambda_function)

        # DynamoDBテーブルのテスト
        dynamodb_results = [test_dynamodb_operations(dynamodb_client, table) for table in dynamodb_tables]
        dynamodb_result = all(dynamodb_results)

        # APIエンドポイントのテスト
        api_result = test_api_endpoint(api_url, api_key)

        # すべてのテストが成功した場合
        if lambda_result and dynamodb_result and api_result:
            logger.info("All smoke tests passed successfully")
            return {
                'status': 'success',
                'message': 'All smoke tests passed successfully'
            }
        else:
            error_message = "Some smoke tests failed"
            logger.error(error_message)
            return {
                'status': 'error',
                'message': error_message
            }

    except Exception as e:
        error_message = f"Error during smoke tests: {str(e)}"
        logger.error(error_message)
        return {
            'status': 'error',
            'message': error_message
        }

if __name__ == "__main__":
    result = main()
    print(json.dumps(result)) 