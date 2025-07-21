import json
from datetime import datetime


def set_alert(request):
    """Cloud Functions用 価格アラート設定エンドポイント"""
    if request.method != 'POST':
        return (json.dumps({"error": "Method Not Allowed"}), 405, {'Content-Type': 'application/json'})
    # ここで実際のアラート設定処理を呼び出す（ダミー実装）
    result = {
        "message": "Alert set successfully",
        "timestamp": datetime.now().isoformat()
    }
    headers = {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store'
    }
    return (json.dumps(result, default=str), 200, headers) 