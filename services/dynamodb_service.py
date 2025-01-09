import boto3
from boto3.dynamodb.conditions import Key

# DynamoDBテーブル名を指定
DYNAMODB_TABLE_NAME = "official_prices"

def get_prices_by_series(series_name):
    """指定されたシリーズの買取価格を取得"""
    try:
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table(DYNAMODB_TABLE_NAME)

        # クエリ実行
        response = table.query(
            KeyConditionExpression=Key("series").eq(series_name)
        )
        return response.get("Items", [])
    except Exception as e:
        print(f"Error querying DynamoDB: {str(e)}")
        raise
