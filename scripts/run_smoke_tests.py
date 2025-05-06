#!/usr/bin/env python3

"""
使用方法:
このスクリプトは、スモークテストの実行に使用されます。
以下のコマンドで実行します：
    python3 run_smoke_tests.py

必要な環境変数:
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- AWS_DEFAULT_REGION
- LAMBDA_FUNCTION_NAME: テスト対象のLambda関数名
- DYNAMODB_TABLES: テスト対象のDynamoDBテーブル名のJSON配列
- API_URL: テスト対象のAPIエンドポイントURL

テスト内容:
1. Lambda関数の呼び出しテスト
2. DynamoDBの基本操作テスト
3. APIエンドポイントのテスト
"""

import json
import logging
import os

import boto3
import requests

# ロギングの設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWSクライアントの初期化
lambda_client = boto3.client('lambda')
dynamodb_client = boto3.client('dynamodb')

def test_lambda_invocation(function_name):
    """Lambda関数の呼び出しテスト"""
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse'
        )
        if response['StatusCode'] == 200:
            logger.info(f"Lambda function {function_name} invocation successful")
            return True
        else:
            logger.error(f"Lambda function {function_name} invocation failed")
            return False
    except Exception as e:
        logger.error(f"Error testing Lambda function {function_name}: {str(e)}")
        return False

def test_dynamodb_operations(table_names):
    """DynamoDBの基本操作テスト"""
    try:
        for table_name in table_names:
            # テーブルの状態確認
            response = dynamodb_client.describe_table(TableName=table_name)
            if response['Table']['TableStatus'] != 'ACTIVE':
                logger.error(f"DynamoDB table {table_name} is not active")
                return False

            # サンプルデータのスキャン
            response = dynamodb_client.scan(
                TableName=table_name,
                Limit=1
            )
            logger.info(f"DynamoDB table {table_name} scan successful")
        return True
    except Exception as e:
        logger.error(f"Error testing DynamoDB operations: {str(e)}")
        return False

def test_api_endpoint(api_url):
    """APIエンドポイントのテスト"""
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            logger.info(f"API endpoint {api_url} test successful")
            return True
        else:
            logger.error(f"API endpoint {api_url} test failed with status code {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error testing API endpoint {api_url}: {str(e)}")
        return False

def main():
    """メイン関数"""
    try:
        # 環境変数から設定を取得
        lambda_function_name = os.environ['LAMBDA_FUNCTION_NAME']
        dynamodb_tables = json.loads(os.environ['DYNAMODB_TABLES'])
        api_url = os.environ['API_URL']

        # 各テストを実行
        lambda_test = test_lambda_invocation(lambda_function_name)
        dynamodb_test = test_dynamodb_operations(dynamodb_tables)
        api_test = test_api_endpoint(api_url)

        # すべてのテストが成功した場合
        if lambda_test and dynamodb_test and api_test:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'All smoke tests passed',
                    'lambda_function': lambda_function_name,
                    'dynamodb_tables': dynamodb_tables,
                    'api_url': api_url
                })
            }
        else:
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'message': 'Some smoke tests failed',
                    'lambda_function': lambda_function_name,
                    'dynamodb_tables': dynamodb_tables,
                    'api_url': api_url
                })
            }

    except Exception as e:
        logger.error(f"Error in smoke testing process: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': f'Smoke testing failed: {str(e)}'
            })
        }

if __name__ == "__main__":
    result = main()
    print(json.dumps(result)) 