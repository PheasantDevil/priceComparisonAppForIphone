#!/usr/bin/env python3
"""
Firestore権限テストスクリプト
- 書き込み権限の確認
- 削除権限の確認
- 詳細なエラー情報の提供
"""

import json
import sys

from google.cloud import firestore
from google.oauth2 import service_account


def test_firestore_permissions():
    """Firestoreの権限をテスト"""
    try:
        print("Testing Firestore permissions...")
        
        # 認証情報の設定
        print("Setting up credentials...")
        credentials = service_account.Credentials.from_service_account_file('key.json')
        print(f"✓ Credentials loaded successfully")
        print(f"  Service account: {credentials.service_account_email}")
        
        # Firestoreクライアントの初期化
        print("Initializing Firestore client...")
        db = firestore.Client(credentials=credentials)
        print("✓ Firestore client initialized")
        
        # テスト用ドキュメントを作成
        print("Testing write permissions...")
        test_data = {
            'test': 'permission_check', 
            'timestamp': 'test',
            'description': 'Temporary test document for permission verification'
        }
        
        doc_ref = db.collection('kaitori_prices').document()
        doc_ref.set(test_data)
        print('✓ Write permission test successful')
        
        # テスト用ドキュメントを削除
        print("Testing delete permissions...")
        doc_ref.delete()
        print('✓ Delete permission test successful')
        
        # 読み取り権限もテスト
        print("Testing read permissions...")
        docs = db.collection('kaitori_prices').limit(1).stream()
        doc_count = len(list(docs))
        print(f'✓ Read permission test successful (found {doc_count} documents)')
        
        print('✓ All Firestore permission tests passed')
        return True
        
    except Exception as e:
        print(f'✗ Permission test failed: {e}')
        print(f'Error type: {type(e).__name__}')
        print(f'Error details: {str(e)}')
        
        # 認証情報の詳細を表示
        try:
            if 'credentials' in locals():
                print(f'Service account email: {credentials.service_account_email}')
                print(f'Project ID: {credentials.project_id}')
        except Exception as auth_error:
            print(f'Could not get credential details: {auth_error}')
        
        return False

if __name__ == "__main__":
    success = test_firestore_permissions()
    sys.exit(0 if success else 1) 