import json
import logging
import os
from datetime import datetime, timezone
from decimal import Decimal

import boto3
from botocore.exceptions import ClientError

# ロガーの設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# DynamoDBクライアントの初期化
dynamodb = boto3.resource('dynamodb')
kaitori_table = dynamodb.Table(os.environ.get('KAITORI_TABLE', 'kaitori_prices'))
official_table = dynamodb.Table(os.environ.get('OFFICIAL_TABLE', 'official_prices'))

# シリーズごとの有効な容量を定義
VALID_CAPACITIES = {
    "iPhone 16": ["128GB", "256GB", "512GB"],
    "iPhone 16 Pro": ["128GB", "256GB", "512GB", "1TB"],
    "iPhone 16 Pro Max": ["256GB", "512GB", "1TB"],
    "iPhone 16e": ["128GB", "256GB", "512GB"]
}

def safe_int(val):
    """Convert any numeric type to integer safely"""
    if val is None:
        return 0
    if isinstance(val, (int, float, Decimal)):
        return int(val)
    try:
        return int(str(val))
    except (ValueError, TypeError):
        logger.warning(f"Could not convert value to int: {val}")
        return 0

def lambda_handler(event, context):
    """
    Lambda関数のメインハンドラー
    """
    try:
        logger.info("Starting price retrieval process")
        logger.info(f"Event: {json.dumps(event)}")
        
        # クエリパラメータからシリーズを取得
        series = event.get('queryStringParameters', {}).get('series', 'iPhone 16')
        logger.info(f"Retrieving prices for series: {series}")
        
        # シリーズが有効かチェック
        if series not in VALID_CAPACITIES:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                    'Access-Control-Allow-Methods': 'GET,OPTIONS'
                },
                'body': json.dumps({
                    'message': f'Invalid series: {series}. Valid series are: {", ".join(VALID_CAPACITIES.keys())}'
                })
            }
        
        # 価格情報を取得
        prices = get_prices(series)
        logger.info(f"Retrieved prices: {json.dumps(prices)}")
        
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
        logger.error(f"Error in lambda_handler: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET,OPTIONS'
            },
            'body': json.dumps({'message': 'Internal server error', 'error': str(e)})
        }

def get_prices(series):
    """
    指定されたシリーズの全容量の価格情報を取得
    """
    try:
        logger.info(f"Getting official prices for series: {series}")
        # 公式価格の取得（seriesでquery）
        official_response = official_table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('series').eq(series)
        )
        official_items = official_response.get('Items', [])
        logger.info(f"Official items: {official_items}")

        logger.info(f"Getting kaitori prices for series: {series}")
        # 買取価格の取得（seriesでquery）
        kaitori_response = kaitori_table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('series').eq(series)
        )
        kaitori_items = kaitori_response.get('Items', [])
        logger.info(f"Kaitori items: {kaitori_items}")

        # 公式価格をマッピング
        official_prices = {}
        if official_items:
            official_item = official_items[0]  # シリーズごとに1つのアイテム
            if 'price' in official_item:
                official_prices = official_item['price']

        # 買取価格をマッピング
        kaitori_map = {item['capacity']: item for item in kaitori_items}

        prices = {}
        for capacity in VALID_CAPACITIES.get(series, []):
            # 公式価格
            official_price = safe_int(official_prices.get(capacity, 0))

            # 買取価格
            kaitori_price = 0
            kaitori_item = kaitori_map.get(capacity)
            if kaitori_item:
                kaitori_price = safe_int(kaitori_item.get('kaitori_price_max', 0))

            prices[capacity] = {
                'official_price': official_price,
                'kaitori_price': kaitori_price,
                'price_diff': kaitori_price - official_price,
                'rakuten_diff': kaitori_price - int(official_price * 0.9)
            }

        return {
            'series': series,
            'prices': prices
        }

    except ClientError as e:
        logger.error(f"Error getting prices: {str(e)}", exc_info=True)
        raise
