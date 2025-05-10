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
kaitori_table = dynamodb.Table(os.environ['KAITORI_TABLE'])
official_table = dynamodb.Table(os.environ['OFFICIAL_TABLE'])

# シリーズごとの有効な容量を定義
VALID_CAPACITIES = {
    "iPhone 16": ["128GB", "256GB", "512GB"],
    "iPhone 16 Plus": ["128GB", "256GB", "512GB"],
    "iPhone 16 Pro": ["128GB", "256GB", "512GB", "1TB"],
    "iPhone 16 Pro Max": ["256GB", "512GB", "1TB"],
    "iPhone 16 e": ["128GB", "256GB", "512GB"]
}

def lambda_handler(event, context):
    """
    Lambda関数のメインハンドラー
    """
    try:
        logger.info("Starting price retrieval process")
        
        # クエリパラメータからシリーズを取得
        series = event.get('queryStringParameters', {}).get('series', 'iPhone 16')
        
        # 価格情報を取得
        prices = get_prices(series)
        
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

def get_prices(series):
    """
    指定されたシリーズの全容量の価格情報を取得
    """
    try:
        # 公式価格の取得
        official_response = official_table.scan(
            FilterExpression='#s = :series',
            ExpressionAttributeNames={'#s': 'series'},
            ExpressionAttributeValues={':series': series}
        )
        
        # 買取価格の取得
        kaitori_response = kaitori_table.scan(
            FilterExpression='#s = :series',
            ExpressionAttributeNames={'#s': 'series'},
            ExpressionAttributeValues={':series': series}
        )
        
        # データの整形と差分計算
        prices = {}
        for capacity in VALID_CAPACITIES.get(series, []):
            official_price = next(
                (item['price'] for item in official_response['Items'] 
                 if item['capacity'] == capacity), 
                None
            )
            kaitori_price = next(
                (item['price'] for item in kaitori_response['Items'] 
                 if item['capacity'] == capacity), 
                None
            )
            
            if official_price and kaitori_price:
                prices[capacity] = {
                    'official_price': official_price,
                    'kaitori_price': kaitori_price,
                    'price_diff': kaitori_price - official_price,
                    'rakuten_diff': kaitori_price - (official_price * 0.9)
                }
        
        return {
            'series': series,
            'prices': prices
        }
        
    except ClientError as e:
        logger.error(f"Error getting prices: {str(e)}")
        raise
