import json
from datetime import datetime, timedelta

from google.cloud import firestore


def get_price_history(request):
    """Cloud Functions用 価格推移データ取得エンドポイント (Firestore版)"""
    db = firestore.Client()
    series = request.args.get('series')
    capacity = request.args.get('capacity')
    days = int(request.args.get('days', 14))
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Firestoreのprice_historyコレクションから該当データを取得
    query = db.collection('price_history')
    if series:
        query = query.where('series', '==', series)
    if capacity:
        query = query.where('capacity', '==', capacity)
    query = query.where('date', '>=', start_date.strftime('%Y-%m-%d'))
    docs = query.stream()
    history = [doc.to_dict() for doc in docs]
    result = {
        'series': series,
        'capacity': capacity,
        'days': days,
        'history': history
    }
    headers = {
        'Content-Type': 'application/json',
        'Cache-Control': 'public, max-age=300'
    }
    return (json.dumps(result, default=str), 200, headers) 