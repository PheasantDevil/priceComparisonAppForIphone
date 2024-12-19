import json
import logging
from decimal import Decimal

import boto3

# ロガーの設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-1')
table = dynamodb.Table('official_prices')

# Decimal型を処理するカスタムエンコーダ
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            # Decimalをfloatまたはintに変換
            return float(obj) if obj % 1 else int(obj)
        return super(DecimalEncoder, self).default(obj)

def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")
    try:
        # クエリパラメータの取得
        query_params = event.get("queryStringParameters", {})
        series = query_params.get("series", "iPhone 16")
        logger.info(f"Querying series: {series}")

        # DynamoDBクエリ
        response = table.query(
            KeyConditionExpression="series = :series",
            ExpressionAttributeValues={":series": series}
        )
        
        # データ整形
        items = response.get('Items', [])
        logger.info(f"Query result: {items}")

        # JSONレスポンスの生成
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(items, cls=DecimalEncoder, ensure_ascii=False)
        }

    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}, ensure_ascii=False)
        }
