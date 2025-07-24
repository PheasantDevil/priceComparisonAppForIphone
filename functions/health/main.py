import json
import os
from datetime import datetime


def health(request):
    """Cloud Functions用 ヘルスチェックエンドポイント"""
    result = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv('APP_ENV', 'production'),
        "version": "1.0.0"
    }
    headers = {
        'Content-Type': 'application/json',
        'Cache-Control': 'public, max-age=60'
    }
    return (json.dumps(result, default=str), 200, headers) 