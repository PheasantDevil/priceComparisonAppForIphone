#!/usr/bin/env python3
"""
Firestore権限テストスクリプト
- 書き込み権限の確認
- 削除権限の確認
"""

import json

from google.cloud import firestore
from google.oauth2 import service_account


def test_firestore_permissions():
    """Firestoreの権限をテスト"""
    try:
        print("Testing Firestore permissions...")
        
        # 認証情報の設定
        credentials = service_account.Credentials.from_service_account_file('key.json')
        db = firestore.Client(credentials=credentials)
        
        # テスト用ドキュメントを作成
        test_data = {
            'test': 'permission_check', 
            'timestamp': 'test',
            'description': 'Temporary test document for permission verification'
        }
        
        doc_ref = db.collection('kaitori_prices').document()
        doc_ref.set(test_data)
        print('✓ Write permission test successful')
        
        # テスト用ドキュメントを削除
        doc_ref.delete()
        print('✓ Delete permission test successful')
        
        print('✓ All Firestore permission tests passed')
        return True
        
    except Exception as e:
        print(f'✗ Permission test failed: {e}')
        return False

if __name__ == "__main__":
    success = test_firestore_permissions()
    exit(0 if success else 1) 