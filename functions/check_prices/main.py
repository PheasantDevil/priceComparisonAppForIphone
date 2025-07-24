import json
from datetime import datetime


def check_prices(request):
    """Cloud Functions用 価格チェックエンドポイント"""
    if request.method != 'GET':
        return (json.dumps({"error": "Method Not Allowed"}), 405, {'Content-Type': 'application/json'})
    # ここで実際の価格チェック処理を呼び出す（ダミー実装）
    result = {
        "message": "Price check completed",
        "timestamp": datetime.now().isoformat()
    }
    headers = {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store'
    }
    return (json.dumps(result, default=str), 200, headers) 