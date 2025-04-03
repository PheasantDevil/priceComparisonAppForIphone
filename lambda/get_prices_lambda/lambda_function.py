import json
import logging
import traceback
from decimal import Decimal

from apple_scraper_for_rudea import DecimalEncoder, get_kaitori_prices

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # クエリパラメータからseriesを取得
        query_params = event.get('queryStringParameters', {})
        if not query_params:
            logger.error("No query parameters found")
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET,OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
                },
                'body': json.dumps({'error': 'Query parameters are required'})
            }

        series = query_params.get('series')
        if not series:
            logger.error("Series parameter is missing")
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET,OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
                },
                'body': json.dumps({'error': 'series parameter is required'})
            }

        logger.info(f"Fetching prices for series: {series}")
        
        # 価格データを取得
        prices = get_kaitori_prices(series=series)
        
        logger.info(f"Retrieved prices: {prices}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET,OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
            },
            'body': json.dumps(prices, cls=DecimalEncoder)
        }

    except Exception as e:
        error_traceback = traceback.format_exc()
        logger.error(f"Error: {str(e)}\nTraceback: {error_traceback}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET,OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
            },
            'body': json.dumps({
                'error': str(e),
                'detail': 'An error occurred while processing your request',
                'traceback': error_traceback
            }, cls=DecimalEncoder)
        }
