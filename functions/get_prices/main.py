import json
import os
from datetime import datetime

from common.cors import get_cors_headers, handle_cors_request
from google.cloud import firestore


def get_prices(request):
    """Cloud Functions用 価格データ取得エンドポイント (Firestore版)"""
    # CORS preflight request handling
    cors_response = handle_cors_request(request)
    if cors_response:
        return cors_response
    
    db = firestore.Client()
    series = request.args.get('series')
    
    # 買取価格データを取得
    kaitori_prices_ref = db.collection('kaitori_prices')
    kaitori_query = kaitori_prices_ref
    if series:
        kaitori_query = kaitori_query.where('series', '==', series)
    kaitori_docs = kaitori_query.stream()
    
    # 公式価格データを取得
    official_prices_ref = db.collection('official_prices')
    if series:
        # シリーズ名でドキュメントIDを検索
        doc_ref = official_prices_ref.document(series)
        doc_snapshot = doc_ref.get()
        print(f"Document exists: {doc_snapshot.exists}")
        if doc_snapshot.exists:
            print(f"Document data: {doc_snapshot.to_dict()}")
        official_docs = [doc_snapshot] if doc_snapshot.exists else []
    else:
        official_docs = official_prices_ref.stream()
    
    # データを整理
    kaitori_data = {}
    for doc in kaitori_docs:
        data = doc.to_dict()
        series_name = data.get('series')
        if series_name not in kaitori_data:
            kaitori_data[series_name] = {}
        
        capacity = data.get('capacity')
        kaitori_data[series_name][capacity] = {
            'kaitori_price_min': data.get('kaitori_price_min', 0),
            'kaitori_price_max': data.get('kaitori_price_max', 0),
            'colors': data.get('colors', {})
        }
    
    official_data = {}
    for doc in official_docs:
        data = doc.to_dict()
        series_name = doc.id  # ドキュメントIDがシリーズ名
        if series_name not in official_data:
            official_data[series_name] = {}
        
        # データ構造: {'price': {'256GB': {'colors': {...}}}}
        price_data = data.get('price', {})
        for capacity, capacity_data in price_data.items():
            # 各容量の色の価格から平均価格を計算
            colors = capacity_data.get('colors', {})
            if colors:
                avg_price = sum(colors.values()) / len(colors)
                official_data[series_name][capacity] = {
                    'official_price': int(avg_price)
                }
    
    # デバッグ用ログ
    print(f"Official data for {series}: {official_data}")
    
    # フロントエンドが期待する形式に変換
    result = {}
    for series_name in kaitori_data:
        if series_name not in result:
            result[series_name] = {
                'series': series_name,
                'prices': {}
            }
        
        for capacity in kaitori_data[series_name]:
            kaitori_info = kaitori_data[series_name][capacity]
            official_info = official_data.get(series_name, {}).get(capacity, {})
            
            official_price = official_info.get('official_price', 0)
            kaitori_price = kaitori_info.get('kaitori_price_max', 0)  # 最大買取価格を使用
            price_diff = kaitori_price - official_price
            rakuten_diff = kaitori_price - (official_price * 0.9)
            
            result[series_name]['prices'][capacity] = {
                'official_price': official_price,
                'kaitori_price': kaitori_price,
                'price_diff': price_diff,
                'rakuten_diff': rakuten_diff
            }
    
    # シリーズ指定の場合は単一オブジェクトを返す
    if series and series in result:
        response_data = result[series]
    else:
        response_data = result
    
    # CORSヘッダーを含むヘッダーを設定
    headers = {
        'Content-Type': 'application/json',
        'Cache-Control': 'public, max-age=300',
        **get_cors_headers()
    }
    return (json.dumps(response_data, default=str), 200, headers) 