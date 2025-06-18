#!/usr/bin/env python3
"""
Firestoreの公式価格データをエクスポートするスクリプト
"""

import json

from google.cloud import firestore
from google.oauth2 import service_account


def export_official_prices():
    credentials = service_account.Credentials.from_service_account_file('key.json')
    db = firestore.Client(credentials=credentials)

    docs = db.collection('official_prices').stream()
    all_data = []
    
    for doc in docs:
        data = doc.to_dict()
        print(f"Series: {doc.id}")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        all_data.append({
            'series': doc.id,
            'data': data
        })

    with open('official_prices_export.json', 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    print(f"Exported {len(all_data)} documents to official_prices_export.json")

if __name__ == "__main__":
    export_official_prices() 