import json
import os
from datetime import datetime
from common.cors import get_cors_headers, handle_cors_request


def health(request):
    """Cloud Functions用 ヘルスチェックエンドポイント"""
    # CORS preflight request handling
    cors_response = handle_cors_request(request)
    if cors_response:
        return cors_response
    
    result = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv('APP_ENV', 'production'),
        "version": "1.0.0"
    }
    headers = {
        'Content-Type': 'application/json',
        'Cache-Control': 'public, max-age=60',
        **get_cors_headers()
    }
    return (json.dumps(result, default=str), 200, headers) 