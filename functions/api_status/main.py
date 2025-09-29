import json
import os
from datetime import datetime

from common.cors import get_cors_headers, handle_cors_request
from google.cloud import firestore


def api_status(request):
    """Cloud Functions用 APIステータスエンドポイント"""
    # CORS preflight request handling
    cors_response = handle_cors_request(request)
    if cors_response:
        return cors_response
    
    # Firestore接続確認
    try:
        firestore.Client().collection('_health_check').limit(1).get()
        db_status = "connected"
    except Exception as e:
        print(f"Firestore connection failed: {e}")  # Log for debugging
        db_status = "disconnected"
    # Storage接続確認（省略可、必要ならgoogle-cloud-storageで実装）
    storage_status = os.getenv('BUCKET_NAME', None)
    result = {
        "status": "operational",
        "services": {
            "api": "running",
            "database": db_status,
            "storage": "configured" if storage_status else "not_configured"
        },
        "timestamp": datetime.now().isoformat()
    }
    headers = {
        'Content-Type': 'application/json',
        'Cache-Control': 'public, max-age=60',
        **get_cors_headers()
    }
    return (json.dumps(result, default=str), 200, headers) 