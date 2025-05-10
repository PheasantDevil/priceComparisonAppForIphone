import json
import logging

import boto3

# ロギングの設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Lambda関数のハンドラー
    基本的な機能テストを実行する関数
    """
    try:
        logger.info("Smoke test started")
        
        # DynamoDBクライアントの初期化
        dynamodb = boto3.resource('dynamodb')
        
        # テスト対象のテーブル
        tables = [
            'iphone_prices',
            'official_prices',
            'price_history',
            'price_predictions'
        ]
        
        results = {}
        
        # 各テーブルの存在確認
        for table_name in tables:
            try:
                table = dynamodb.Table(table_name)
                table.load()
                results[table_name] = "exists"
                logger.info(f"Table {table_name} exists")
            except Exception as e:
                results[table_name] = f"error: {str(e)}"
                logger.error(f"Error checking table {table_name}: {str(e)}")
        
        response = {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Smoke test completed",
                "results": results,
                "status": "success"
            })
        }
        
        logger.info("Smoke test completed successfully")
        return response
        
    except Exception as e:
        logger.error(f"Smoke test failed: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "Smoke test failed",
                "error": str(e),
                "status": "error"
            })
        } 