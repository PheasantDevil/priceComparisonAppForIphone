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
        # 公式価格の取得
        official_response = official_table.get_item(
            Key={'series': series}
        )
        
        logger.info(f"Getting kaitori prices for series: {series}")
        # 買取価格の取得
        kaitori_response = kaitori_table.get_item(
            Key={'series': series}
        )
        
        # データの整形と差分計算
        prices = {}
        if 'Item' in official_response and 'Item' in kaitori_response:
            # テーブル構造に合わせてフィールド名を修正
            official_prices = official_response['Item'].get('price', {})
            kaitori_prices = kaitori_response['Item'].get('price', {})
            
            # すべての値をintに変換
            official_prices = {k: safe_int(v) for k, v in official_prices.items()}
            kaitori_prices = {k: safe_int(v) for k, v in kaitori_prices.items()}
            
            for capacity in VALID_CAPACITIES.get(series, []):
                if capacity in official_prices and capacity in kaitori_prices:
                    official_price = official_prices[capacity]
                    kaitori_price = kaitori_prices[capacity]
                    
                    prices[capacity] = {
                        'official_price': official_price,
                        'kaitori_price': kaitori_price,
                        'price_diff': kaitori_price - official_price,
                        'rakuten_diff': kaitori_price - int(official_price * 0.9)
                    }
        else:
            logger.warning(f"Data not found for series: {series}")
            # データが存在しない場合は空の価格情報を返す
            for capacity in VALID_CAPACITIES.get(series, []):
                prices[capacity] = {
                    'official_price': 0,
                    'kaitori_price': 0,
                    'price_diff': 0,
                    'rakuten_diff': 0
                }
        
        return {
            'series': series,
            'prices': prices
        }
        
    except ClientError as e:
        logger.error(f"Error getting prices: {str(e)}", exc_info=True)
        raise
