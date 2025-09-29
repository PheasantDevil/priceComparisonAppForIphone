"""
CORS設定の共通モジュール
"""

def get_cors_headers():
    """CORSヘッダーを取得する"""
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Access-Control-Max-Age': '3600'
    }

def handle_cors_request(request):
    """OPTIONSリクエストを処理する"""
    if request.method == 'OPTIONS':
        headers = get_cors_headers()
        headers['Content-Type'] = 'text/plain'
        return ('', 204, headers)
    return None
