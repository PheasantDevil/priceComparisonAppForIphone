import json
from datetime import datetime


def set_alert(request):
    """Cloud Functions用 価格アラート設定エンドポイント"""
    # CORS headers for frontend integration
    headers = {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST',
        'Access-Control-Allow-Headers': 'Content-Type'
    }

    # Preflight request handling
    if request.method == 'OPTIONS':
        return ('', 204, headers)

    if request.method != 'POST':
        return (json.dumps({"error": "Method Not Allowed"}), 405, headers)

    # Validate request body
    try:
        request_data = request.get_json()
        if not request_data:
            return (json.dumps({"error": "Request body required"}), 400, headers)
    except Exception:
        return (json.dumps({"error": "Invalid JSON"}), 400, headers)

    # ここで実際のアラート設定処理を呼び出す（ダミー実装）
    result = {
        "message": "Alert set successfully",
        "timestamp": datetime.now().isoformat()
    }

    return (json.dumps(result, default=str), 200, headers)