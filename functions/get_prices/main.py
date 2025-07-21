import json
import os
from datetime import datetime

from google.cloud import firestore


def get_prices(request):
    """Cloud Functions用 価格データ取得エンドポイント (Firestore版)"""
    db = firestore.Client()
    series = request.args.get('series')
    prices_ref = db.collection('kaitori_prices')
    query = prices_ref
    if series:
        query = query.where('series', '==', series)
    docs = query.stream()
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