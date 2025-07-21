import json
from datetime import datetime


def scrape_prices(request):
    """Cloud Functions用 価格スクレイピングエンドポイント"""
    if request.method != 'POST':
        return (json.dumps({"error": "Method Not Allowed"}), 405, {'Content-Type': 'application/json'})
    # ここで実際のスクレイピング処理を呼び出す（ダミー実装）
    result = {
        "message": "Price scraping initiated",
        "timestamp": datetime.now().isoformat()
    }
    headers = {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store'
    }
    return (json.dumps(result, default=str), 200, headers) 