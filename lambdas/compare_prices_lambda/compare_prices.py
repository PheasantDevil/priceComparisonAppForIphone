import json
from datetime import datetime, timedelta
from typing import Any, Dict, List

import boto3

dynamodb = boto3.resource('dynamodb')
price_history_table = dynamodb.Table('price_history')

def get_price_history(model_id: str, days: int = 30) -> List[Dict[str, Any]]:
    """指定されたモデルの価格履歴を取得"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    response = price_history_table.query(
        IndexName='DateIndex',
        KeyConditionExpression='model = :model AND #date BETWEEN :start AND :end',
        ExpressionAttributeNames={
            '#date': 'date'
        },
        ExpressionAttributeValues={
            ':model': model_id,
            ':start': start_date.strftime('%Y-%m-%d'),
            ':end': end_date.strftime('%Y-%m-%d')
        }
    )
    
    return sorted(response['Items'], key=lambda x: x['date'])

def compare_prices(model_ids: List[str], days: int = 30) -> Dict[str, Any]:
    """複数モデルの価格を比較"""
    results = {}
    
    for model_id in model_ids:
        price_history = get_price_history(model_id, days)
        if not price_history:
            continue
            
        prices = [float(item['price']) for item in price_history]
        current_price = prices[-1]
        min_price = min(prices)
        max_price = max(prices)
        avg_price = sum(prices) / len(prices)
        
        # 価格変動率の計算
        if len(prices) > 1:
            price_change = ((current_price - prices[0]) / prices[0]) * 100
        else:
            price_change = 0
            
        results[model_id] = {
            'current_price': current_price,
            'min_price': min_price,
            'max_price': max_price,
            'avg_price': avg_price,
            'price_change': price_change,
            'price_history': price_history
        }
    
    return results

def lambda_handler(event, context):
    try:
        # クエリパラメータからモデルIDを取得
        models = event.get('queryStringParameters', {}).get('models', '')
        if not models:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Model IDs are required'})
            }
            
        model_ids = models.split(',')
        
        # 比較期間を取得（デフォルト30日）
        days = int(event.get('queryStringParameters', {}).get('days', 30))
        
        # 価格比較を実行
        results = compare_prices(model_ids, days)
        
        return {
            'statusCode': 200,
            'body': json.dumps(results)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        } 