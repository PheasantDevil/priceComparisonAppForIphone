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
    try:
        # クエリパラメータを取得
        query_parameters = event.get('queryStringParameters', {})
        series = query_parameters.get('series')

        if not series:
            return {
                "statusCode": 400,
                "headers": {
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({"error": "Missing 'series' query parameter"})
            }

        # データ取得処理
        prices = get_prices_from_dynamodb(series)

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps(prices)
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({"error": str(e)})
        }
