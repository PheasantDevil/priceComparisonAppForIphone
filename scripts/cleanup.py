#!/usr/bin/env python3

"""
使用方法:
このスクリプトは、AWSリソースのクリーンアップを実行します。
以下のコマンドで実行します：
    python3 cleanup.py

必要な環境変数:
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- AWS_DEFAULT_REGION

クリーンアップ手順:
1. DynamoDBテーブルのデータ削除
2. Terraformによるリソースの削除
3. クリーンアップの検証
"""

import json
import logging
import os
import subprocess
import sys
import time

import boto3

# ロギングの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_command(command, cwd=None):
    """コマンドを実行し、結果を返す"""
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, f"Error executing command: {e.stderr}"

def cleanup_dynamodb_tables():
    """DynamoDBテーブルのデータを削除"""
    logger.info("Cleaning up DynamoDB tables...")
    
    dynamodb = boto3.client('dynamodb')
    tables = [
        'iphone_prices',
        'official_prices',
        'price_comparison',
        'price_history',
        'price_predictions',
        'kaitori_prices'
    ]

    for table_name in tables:
        try:
            # テーブルの存在確認
            try:
                dynamodb.describe_table(TableName=table_name)
            except dynamodb.exceptions.ResourceNotFoundException:
                logger.info(f"Table {table_name} does not exist, skipping...")
                continue

            # テーブルのスキャン
            response = dynamodb.scan(TableName=table_name)
            items = response.get('Items', [])

            # バッチ削除
            with dynamodb.batch_writer(TableName=table_name) as batch:
                for item in items:
                    batch.delete_item(Key={k: v for k, v in item.items() if k in ['model', 'timestamp']})

            logger.info(f"Cleaned up table {table_name}")
        except Exception as e:
            logger.error(f"Error cleaning up table {table_name}: {e}")
            return False

    return True

def run_terraform_destroy():
    """Terraformでリソースを削除"""
    logger.info("Running Terraform destroy...")
    
    success, output = run_command(["terraform", "destroy", "-auto-approve"], cwd="terraform")
    if not success:
        logger.error(f"Failed to destroy Terraform resources: {output}")
        return False
    logger.info("Terraform resources destroyed successfully")
    return True

def verify_cleanup():
    """クリーンアップを検証"""
    logger.info("Verifying cleanup...")
    
    dynamodb = boto3.client('dynamodb')
    tables = [
        'iphone_prices',
        'official_prices',
        'price_comparison',
        'price_history',
        'price_predictions',
        'kaitori_prices'
    ]

    for table_name in tables:
        try:
            # テーブルの存在確認
            try:
                response = dynamodb.describe_table(TableName=table_name)
                # テーブルが存在する場合、アイテム数を確認
                count = dynamodb.scan(TableName=table_name, Select='COUNT')
                if count['Count'] > 0:
                    logger.error(f"Table {table_name} still contains {count['Count']} items")
                    return False
            except dynamodb.exceptions.ResourceNotFoundException:
                logger.info(f"Table {table_name} does not exist (expected)")
                continue
        except Exception as e:
            logger.error(f"Error verifying table {table_name}: {e}")
            return False

    logger.info("Cleanup verification successful")
    return True

def main():
    """メイン関数"""
    try:
        # 必要な環境変数の確認
        required_env_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_DEFAULT_REGION']
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        if missing_vars:
            logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            return 1

        # クリーンアップ手順の実行
        steps = [
            ("Cleaning up DynamoDB tables", cleanup_dynamodb_tables),
            ("Running Terraform destroy", run_terraform_destroy),
            ("Verifying cleanup", verify_cleanup)
        ]

        for step_name, step_func in steps:
            logger.info(f"Starting: {step_name}")
            if not step_func():
                logger.error(f"Failed: {step_name}")
                return 1
            logger.info(f"Completed: {step_name}")

        logger.info("Cleanup completed successfully")
        return 0

    except Exception as e:
        logger.error(f"Unexpected error during cleanup: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 