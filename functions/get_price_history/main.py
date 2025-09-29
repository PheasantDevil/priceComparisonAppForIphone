import json
from datetime import datetime, timedelta

from google.cloud import firestore
from common.cors import get_cors_headers, handle_cors_request


def get_price_history(request):
    """Cloud Functions用 価格推移データ取得エンドポイント (Firestore版)"""
    # CORS preflight request handling
    cors_response = handle_cors_request(request)
    if cors_response:
        return cors_response
    
    # Input validation
    series = request.args.get('series')
    capacity = request.args.get('capacity')

    if not series or not capacity:
        headers = {
            'Content-Type': 'application/json',
            **get_cors_headers()
        }
        return (json.dumps({'error': 'series and capacity parameters are required'}), 400, headers)

    try:
        days = int(request.args.get('days', 14))
        if days <= 0 or days > 365:
            raise ValueError("Days must be between 1 and 365")
    except (ValueError, TypeError):
        headers = {
            'Content-Type': 'application/json',
            **get_cors_headers()
        }
        return (json.dumps({'error': 'days parameter must be a valid positive integer'}), 400, headers)

    db = firestore.Client()
    end_date = datetime.now()  # Use local time to match data storage
    start_date = end_date - timedelta(days=days)

    try:
        # Firestoreのprice_historyコレクションから該当データを取得
        query = db.collection('price_history')
        if series:
            query = query.where('series', '==', series)
        if capacity:
            query = query.where('capacity', '==', capacity)
        query = query.where('date', '>=', start_date.strftime('%Y-%m-%d'))
        docs = query.stream()
        history = [doc.to_dict() for doc in docs]
        
        # Sort by timestamp for consistent ordering
        history.sort(key=lambda x: x.get('timestamp', 0))
        
    except Exception as e:
        headers = {
            'Content-Type': 'application/json',
            **get_cors_headers()
        }
        return (
            json.dumps({'error': f'Database query failed: {str(e)}'}), 
            500, 
            headers
        )

    result = {
        'series': series,
        'capacity': capacity,
        'days': days,
        'history': history
    }
    headers = {
        'Content-Type': 'application/json',
        'Cache-Control': 'public, max-age=300',
        **get_cors_headers()
    }
    return (json.dumps(result, default=str), 200, headers)