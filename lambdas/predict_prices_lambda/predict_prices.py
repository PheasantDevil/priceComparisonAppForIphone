import json
from datetime import datetime, timedelta
from typing import Any, Dict, List

import boto3
import numpy as np

dynamodb = boto3.resource('dynamodb')
price_history_table = dynamodb.Table('price_history')
price_predictions_table = dynamodb.Table('price_predictions')

def calculate_linear_regression(x: List[float], y: List[float]) -> tuple:
    """単純な線形回帰を計算"""
    n = len(x)
    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(xi * yi for xi, yi in zip(x, y))
    sum_x2 = sum(xi * xi for xi in x)
    
    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
    intercept = (sum_y - slope * sum_x) / n
    
    return slope, intercept

def predict_prices(model_id: str, days: int = 7) -> Dict[str, Any]:
    """価格予測を実行"""
    # 過去30日分の価格データを取得
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
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
    
    if not response['Items']:
        return {
            'error': 'No historical data available for prediction'
        }
    
    # データの準備
    prices = sorted(response['Items'], key=lambda x: x['date'])
    x = list(range(len(prices)))
    y = [float(item['price']) for item in prices]
    
    # 線形回帰の計算
    slope, intercept = calculate_linear_regression(x, y)
    
    # 予測の実行
    predictions = []
    last_date = datetime.strptime(prices[-1]['date'], '%Y-%m-%d')
    
    for i in range(1, days + 1):
        prediction_date = last_date + timedelta(days=i)
        predicted_price = slope * (len(prices) + i) + intercept
        
        # 信頼区間の計算（簡易版）
        std_dev = np.std(y)
        confidence_interval = 1.96 * std_dev / np.sqrt(len(y))
        
        predictions.append({
            'date': prediction_date.strftime('%Y-%m-%d'),
            'predicted_price': round(predicted_price, 2),
            'confidence_interval': round(confidence_interval, 2)
        })
        
        # 予測結果をキャッシュ
        price_predictions_table.put_item(
            Item={
                'model_id': model_id,
                'prediction_date': prediction_date.strftime('%Y-%m-%d'),
                'predicted_price': round(predicted_price, 2),
                'confidence_interval': round(confidence_interval, 2),
                'expiration_time': int((datetime.now() + timedelta(days=1)).timestamp())
            }
        )
    
    return {
        'model_id': model_id,
        'predictions': predictions,
        'trend': 'up' if slope > 0 else 'down' if slope < 0 else 'stable',
        'trend_strength': abs(slope)
    }

def lambda_handler(event, context):
    try:
        # クエリパラメータからモデルIDを取得
        model_id = event.get('queryStringParameters', {}).get('model')
        if not model_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Model ID is required'})
            }
        
        # 予測期間を取得（デフォルト7日）
        days = int(event.get('queryStringParameters', {}).get('days', 7))
        
        # 予測を実行
        result = predict_prices(model_id, days)
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        } 