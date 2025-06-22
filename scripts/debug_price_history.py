#!/usr/bin/env python3
"""
価格履歴データの構造を確認するデバッグスクリプト
"""

import json

from google.cloud import firestore
from google.oauth2 import service_account


def debug_price_history():
    credentials = service_account.Credentials.from_service_account_file('key.json')
    db = firestore.Client(credentials=credentials)
    
    # 価格履歴データを取得
    docs = db.collection('price_history').stream()
    
    print("=== Price History Data Structure ===")
    for i, doc in enumerate(docs):
        if i >= 3:  # 最初の3件のみ表示
            break
        data = doc.to_dict()
        print(f"Document {i+1}:")
        print(f"  ID: {doc.id}")
        print(f"  Data: {json.dumps(data, indent=2, ensure_ascii=False)}")
        print()
    
    # 特定のシリーズと容量の履歴を取得
    query = (
        db.collection('price_history')
        .filter('series', '==', 'iPhone 16 Pro')
        .filter('capacity', '==', '1TB')
    )
    
    docs = query.stream()
    for doc in docs:
        data = doc.to_dict()
        print(f"iPhone 16 Pro 1TB:")
        print(f"  Data: {json.dumps(data, indent=2, ensure_ascii=False)}")
        print()

if __name__ == "__main__":
    debug_price_history() 