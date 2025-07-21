import json
from datetime import datetime


def get_prices(request):
    """Cloud Functions用 価格データ取得エンドポイント"""
    # サンプルデータ
    sample_prices = [
        {
            "id": "iphone-15-pro",
            "name": "iPhone 15 Pro",
            "price": 159800,
            "currency": "JPY",
            "store": "Apple Store",
            "updated_at": datetime.now().isoformat()
        },
        {
            "id": "iphone-15",
            "name": "iPhone 15",
            "price": 119800,
            "currency": "JPY",
            "store": "Apple Store",
            "updated_at": datetime.now().isoformat()
        }
    ]
    headers = {
        'Content-Type': 'application/json',
        'Cache-Control': 'public, max-age=300'
    }
    return (json.dumps(sample_prices), 200, headers) 