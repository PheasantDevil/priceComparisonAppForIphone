import json
import logging
import traceback
from datetime import datetime
from decimal import Decimal

import boto3
import requests
import yaml
from bs4 import BeautifulSoup

from src.apple_scraper_for_rudea import DecimalEncoder, get_kaitori_prices

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def save_kaitori_prices(series, prices):
    """
    買取価格をDynamoDBに保存する
    
    Args:
        series (str): iPhoneのシリーズ名
        prices (dict): 容量ごとの価格データ
        
    Returns:
        bool: 保存が成功したかどうか
    """
    try:
        if not prices:
            logger.warning(f"No prices to save for {series}")
            return False
            
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('iphone_prices')
        
        success_count = 0
        total_count = len(prices)
        
        for capacity, price in prices.items():
            try:
                # 価格が数値でない場合はスキップ
                if not price or not price.isdigit():
                    logger.warning(f"Invalid price format for {series} {capacity}: {price}")
                    continue
                
                item = {
                    'series': series,
                    'capacity': capacity,
                    'price': Decimal(str(price)),
                    'timestamp': datetime.utcnow().isoformat(),
                    'store': 'rudea'  # 店舗情報を追加
                }
                
                table.put_item(Item=item)
                logger.info(f"Saved price for {series} {capacity}: {price}")
                success_count += 1
                
            except Exception as e:
                logger.error(f"Error saving price for {series} {capacity}: {e}")
                logger.error(f"Stack trace: {traceback.format_exc()}")
                continue
        
        logger.info(f"Successfully saved {success_count}/{total_count} prices for {series}")
        return success_count > 0
        
    except Exception as e:
        logger.error(f"Error saving kaitori prices: {e}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        return False

def lambda_handler(event, context):
    """
    Lambda関数のメインハンドラー
    
    Args:
        event (dict): API Gatewayからのイベントデータ
        context (object): Lambda実行コンテキスト
        
    Returns:
        dict: レスポンスデータ
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        logger.info(f"Lambda context: RequestId: {context.aws_request_id}, Function: {context.function_name}, Memory: {context.memory_limit_in_mb}MB")
        
        # クエリパラメータからseriesを取得
        query_params = event.get('queryStringParameters', {})
        if not query_params:
            logger.error("No query parameters found")
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET,OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({
                    'error': 'Query parameters are required',
                    'request_id': context.aws_request_id
                })
            }

        series = query_params.get('series')
        if not series:
            logger.error("Series parameter is missing")
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET,OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({
                    'error': 'series parameter is required',
                    'request_id': context.aws_request_id
                })
            }

        logger.info(f"Fetching prices for series: {series}")
        
        # 価格データを取得
        prices = get_kaitori_prices(series=series)
        logger.info(f"Retrieved prices: {json.dumps(prices, indent=2, cls=DecimalEncoder)}")
        
        # 買取価格が取得できた場合のみDynamoDBに保存
        if series in prices and 'kaitori' in prices[series] and prices[series]['kaitori']:
            save_success = save_kaitori_prices(series, prices[series]['kaitori'])
            if not save_success:
                logger.warning(f"Failed to save some or all prices for {series}")
        else:
            logger.warning(f"No kaitori prices found for {series}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET,OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'data': prices,
                'request_id': context.aws_request_id
            }, cls=DecimalEncoder)
        }

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET,OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': str(e),
                'detail': 'An error occurred while processing your request',
                'request_id': context.aws_request_id,
                'stack_trace': traceback.format_exc()
            }, cls=DecimalEncoder)
        }
