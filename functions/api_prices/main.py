import json
from datetime import datetime

from google.cloud import firestore


def api_prices(request):
    """Cloud Functions用 価格データ取得エンドポイント (Firestore版)"""
    db = firestore.Client()
    # 必要に応じてクエリパラメータでフィルタ可能
    prices_ref = db.collection('official_prices')
    docs = prices_ref.stream()
    result = []
    for doc in docs:
        data = doc.to_dict()
        data['id'] = doc.id
        result.append(data)
    headers = {
        'Content-Type': 'application/json',
        'Cache-Control': 'public, max-age=300'
    }
    return (json.dumps(result, default=str), 200, headers) 