import json
from services.dynamodb_service import get_prices_by_series

def lambda_handler(event, context):
    """Lambda関数のエントリーポイント"""
    try:
        # クエリパラメータからシリーズ名を取得
        series = event.get("queryStringParameters", {}).get("series", "iPhone 16")
        
        # DynamoDBからデータ取得
        prices = get_prices_by_series(series)

        # レスポンスを整形して返却
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(prices)
        }
    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)})
        }
