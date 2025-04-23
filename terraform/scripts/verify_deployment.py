#!/usr/bin/env python3
import json
import logging
import os
import time

import boto3

# ロギングの設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWSクライアントの初期化
lambda_client = boto3.client('lambda')
dynamodb_client = boto3.client('dynamodb')
apigateway_client = boto3.client('apigateway')

def verify_lambda_function(function_name):
    """Lambda関数の状態を確認"""
    try:
        response = lambda_client.get_function(FunctionName=function_name)
        if response['Configuration']['State'] == 'Active':
            logger.info(f"Lambda function {function_name} is active")
            return True
        else:
            logger.error(f"Lambda function {function_name} is not active")
            return False
    except Exception as e:
        logger.error(f"Error verifying Lambda function {function_name}: {str(e)}")
        return False

def verify_dynamodb_tables(table_names):
    """DynamoDBテーブルの状態を確認"""
    try:
        for table_name in table_names:
            response = dynamodb_client.describe_table(TableName=table_name)
            if response['Table']['TableStatus'] == 'ACTIVE':
                logger.info(f"DynamoDB table {table_name} is active")
            else:
                logger.error(f"DynamoDB table {table_name} is not active")
                return False
        return True
    except Exception as e:
        logger.error(f"Error verifying DynamoDB tables: {str(e)}")
        return False

def verify_api_gateway(api_id):
    """API Gatewayのデプロイメント状態を確認"""
    try:
        response = apigateway_client.get_stage(
            restApiId=api_id,
            stageName='production'
        )
        if response['deploymentId']:
            logger.info(f"API Gateway {api_id} is deployed")
            return True
        else:
            logger.error(f"API Gateway {api_id} is not deployed")
            return False
    except Exception as e:
        logger.error(f"Error verifying API Gateway: {str(e)}")
        return False

def lambda_handler(event, context):
    """Lambdaハンドラー関数"""
    try:
        # 環境変数から設定を取得
        lambda_function_name = os.environ['LAMBDA_FUNCTION_NAME']
        dynamodb_tables = json.loads(os.environ['DYNAMODB_TABLES'])
        api_id = os.environ['API_ID']

        # 最大10回のリトライ
        max_retries = 10
        retry_interval = 30  # 秒

        for attempt in range(max_retries):
            logger.info(f"Verification attempt {attempt + 1}/{max_retries}")

            # 各リソースの状態を確認
            lambda_status = verify_lambda_function(lambda_function_name)
            dynamodb_status = verify_dynamodb_tables(dynamodb_tables)
            api_status = verify_api_gateway(api_id)

            # すべてのリソースが正常な場合
            if lambda_status and dynamodb_status and api_status:
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'message': 'All resources are active and deployed',
                        'lambda_function': lambda_function_name,
                        'dynamodb_tables': dynamodb_tables,
                        'api_gateway': api_id
                    })
                }

            # 最後の試行でない場合は待機
            if attempt < max_retries - 1:
                logger.info(f"Waiting {retry_interval} seconds before next attempt...")
                time.sleep(retry_interval)

        # 最大リトライ回数を超えた場合
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Verification failed after maximum retries',
                'lambda_function': lambda_function_name,
                'dynamodb_tables': dynamodb_tables,
                'api_gateway': api_id
            })
        }

    except Exception as e:
        logger.error(f"Error in verification process: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': f'Verification failed: {str(e)}'
            })
        }

if __name__ == "__main__":
    lambda_handler(None, None) 