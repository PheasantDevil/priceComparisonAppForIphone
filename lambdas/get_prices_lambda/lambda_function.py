import json
import logging
import os
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

# ロガーの設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# DynamoDBクライアントの初期化
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

def lambda_handler(event, context):
    """
    Lambda関数のメインハンドラー
    """
    try:
        logger.info("Starting price retrieval process")
        
        # クエリパラメータからシリーズを取得
        series = event.get('queryStringParameters', {}).get('series', 'iPhone 16')
        capacity = event.get('queryStringParameters', {}).get('capacity', '128GB')
        
        # 価格情報を取得
        prices = get_prices(series, capacity)
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET,OPTIONS'
            },
            'body': json.dumps(prices)
        }
        
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET,OPTIONS'
            },
            'body': json.dumps({'error': str(e)})
        }

def get_prices(series, capacity):
    """
    指定されたシリーズと容量の価格情報を取得
    """
    try:
        response = table.scan(
            FilterExpression='#s = :series AND #c = :capacity',
            ExpressionAttributeNames={
                '#s': 'series',
                '#c': 'capacity'
            },
            ExpressionAttributeValues={
                ':series': series,
                ':capacity': capacity
            }
        )
        
        if not response['Items']:
            return {
                'series': series,
                'capacity': capacity,
                'prices': [],
                'message': 'No prices found for this series and capacity'
            }
        
        # レスポンスを整形
        items = []
        for item in response['Items']:
            formatted_item = {
                'series': item['series'],
                'capacity': item['capacity'],
                'price': item['price'],
                'store': item['store'],
                'updated_at': item.get('updated_at', '')
            }
            items.append(formatted_item)
        
        return {
            'series': series,
            'capacity': capacity,
            'prices': items,
            'message': 'Successfully retrieved prices'
        }
        
    except ClientError as e:
        logger.error(f"Error getting prices: {str(e)}")
        raise
