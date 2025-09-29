import json
from datetime import datetime

from common.cors import get_cors_headers, handle_cors_request
from google.cloud import firestore


def api_prices(request):
    """Cloud Functions用 価格データ取得エンドポイント (Firestore版)"""
    # CORS preflight request handling
    cors_response = handle_cors_request(request)
    if cors_response:
        return cors_response
    
    db = firestore.Client()
    # 必要に応じてクエリパラメータでフィルタ可能
    prices_ref = db.collection('official_prices')
    docs = prices_ref.stream()
    result = []
    for doc in docs:
        data = doc.to_dict()
        data['id'] = doc.id
        result.append(data)
    
    # CORSヘッダーを含むヘッダーを設定
    headers = {
        'Content-Type': 'application/json',
        'Cache-Control': 'public, max-age=300',
        **get_cors_headers()
    }
    return (json.dumps(result, default=str), 200, headers) 