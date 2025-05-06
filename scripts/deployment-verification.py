#!/usr/bin/env python3

"""
使用方法:
このスクリプトは、デプロイメント検証の実装に使用されます。
以下のコマンドで実行します：
    python3 deployment-verification.py

必要な環境変数:
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- AWS_DEFAULT_REGION

検証内容:
1. Lambda関数の状態確認
2. DynamoDBテーブルの状態確認
3. API Gatewayの状態確認
"""

import json
import logging
import os
import time

import boto3

# ロギングの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

def verify_lambda_function(lambda_client, function_name):
    """Lambda関数の状態を確認"""
    try:
        response = lambda_client.get_function(FunctionName=function_name)
        state = response['Configuration']['State']
        logger.info(f"Lambda function {function_name} is {state}")
        return state == 'Active'
    except Exception as e:
        logger.error(f"Error verifying Lambda function {function_name}: {e}")
        return False

def verify_dynamodb_tables(dynamodb_client, table_names):
    """DynamoDBテーブルの状態を確認"""
    results = {}
    for table_name in table_names:
        try:
            response = dynamodb_client.describe_table(TableName=table_name)
            status = response['Table']['TableStatus']
            logger.info(f"DynamoDB table {table_name} is {status}")
            results[table_name] = status == 'ACTIVE'
        except Exception as e:
            logger.error(f"Error verifying DynamoDB table {table_name}: {e}")
            results[table_name] = False
    return all(results.values())

def verify_api_gateway(apigateway_client, api_id):
    """API Gatewayの状態を確認"""
    if not api_id:
        logger.error("API ID is not available")
        return False

    try:
        response = apigateway_client.get_rest_api(restApiId=api_id)
        logger.info(f"API Gateway {api_id} is active")
        return True
    except Exception as e:
        logger.error(f"Error verifying API Gateway {api_id}: {e}")
        return False

def main():
    """メイン関数"""
    try:
        # AWSクライアントの初期化
        lambda_client = boto3.client('lambda')
        dynamodb_client = boto3.client('dynamodb')
        apigateway_client = boto3.client('apigateway')

        # 検証対象のリソース
        lambda_functions = ['get_prices']
        dynamodb_tables = ['iphone_prices', 'official_prices']
        api_id = get_api_id()

        # 最大10回のリトライ
        max_retries = 10
        retry_interval = 30  # 秒

        for attempt in range(max_retries):
            logger.info(f"Verification attempt {attempt + 1}/{max_retries}")

            # 各リソースの状態を確認
            lambda_status = all(verify_lambda_function(lambda_client, func) for func in lambda_functions)
            dynamodb_status = verify_dynamodb_tables(dynamodb_client, dynamodb_tables)
            api_status = verify_api_gateway(apigateway_client, api_id)

            # すべてのリソースが正常な場合
            if lambda_status and dynamodb_status and api_status:
                logger.info("All resources are active and ready")
                return {
                    'status': 'success',
                    'message': 'All resources are active and ready'
                }

            # 最後の試行でない場合は待機
            if attempt < max_retries - 1:
                logger.info(f"Waiting {retry_interval} seconds before next attempt...")
                time.sleep(retry_interval)

        # 最大リトライ回数を超えた場合
        error_message = "Verification failed after maximum retries"
        logger.error(error_message)
        return {
            'status': 'error',
            'message': error_message
        }

    except Exception as e:
        error_message = f"Error during verification: {str(e)}"
        logger.error(error_message)
        return {
            'status': 'error',
            'message': error_message
        }

if __name__ == "__main__":
    result = main()
    print(json.dumps(result)) 