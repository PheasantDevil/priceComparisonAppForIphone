#!/usr/bin/env python3
"""
Firestoreのofficial_pricesコレクションの内容を確認するスクリプト
"""

import json
from google.cloud import firestore
from google.oauth2 import service_account

def check_official_prices():
    """official_pricesコレクションの内容を確認"""
    try:
        # 認証情報の設定
        credentials = service_account.Credentials.from_service_account_file('gcp-key.json')
        
        # Firestoreクライアントの初期化
        db = firestore.Client(credentials=credentials)
        
        print("🔍 Firestoreのofficial_pricesコレクションを確認中...")
        print("=" * 60)
        
        # official_pricesコレクションの全ドキュメントを取得
        docs = db.collection('official_prices').stream()
        
        series_count = 0
        for doc in docs:
            series_count += 1
            data = doc.to_dict()
            series_name = doc.id
            
            print(f"\n📱 シリーズ: {series_name}")
            print("-" * 40)
            
            if 'price' in data:
                price_data = data['price']
            else:
                price_data = data
            
            # 各容量の価格を表示
            for capacity, capacity_data in price_data.items():
                print(f"  💾 {capacity}:")
                if 'colors' in capacity_data:
                    for color, price in capacity_data['colors'].items():
                        print(f"    🎨 {color}: ¥{price:,}")
                else:
                    print(f"    💰 価格: ¥{capacity_data:,}")
        
        print(f"\n✅ 合計 {series_count} 個のシリーズが見つかりました")
        
        # iPhone 17シリーズが含まれているかチェック
        print("\n🔍 iPhone 17シリーズの確認:")
        print("=" * 40)
        
        expected_series = [
            "iPhone 17",
            "iPhone 17 Air", 
            "iPhone 17 Pro",
            "iPhone 17 Pro Max"
        ]
        
        # 再度コレクションを取得してiPhone 17シリーズをチェック
        docs = db.collection('official_prices').stream()
        found_series = [doc.id for doc in docs]
        
        for series in expected_series:
            if series in found_series:
                print(f"✅ {series}: 見つかりました")
            else:
                print(f"❌ {series}: 見つかりませんでした")
        
        # 古いiPhone 16シリーズが残っていないかチェック
        print("\n🔍 古いiPhone 16シリーズの確認:")
        print("=" * 40)
        
        old_series = [
            "iPhone 16",
            "iPhone 16 Plus",
            "iPhone 16 Pro", 
            "iPhone 16 Pro Max",
            "iPhone 16 e"
        ]
        
        for series in old_series:
            if series in found_series:
                print(f"⚠️  {series}: まだ残っています")
            else:
                print(f"✅ {series}: 削除されています")
                
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        return False
    
    return True

if __name__ == "__main__":
    check_official_prices()
