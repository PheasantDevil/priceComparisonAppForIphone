import json
import logging
import os
import sys

# srcディレクトリをPythonパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(project_root)

from src.apple_scraper_for_rudea import get_kaitori_prices

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    try:
        logger.info("Lambda function started")
        logger.info(f"Event: {json.dumps(event)}")
        
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
            'body': json.dumps(prices)
        }

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET,OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
            },
            'body': json.dumps({
                'error': str(e),
                'detail': 'An error occurred while processing your request'
            })
        }
