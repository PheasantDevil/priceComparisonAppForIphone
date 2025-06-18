#!/usr/bin/env python3
"""
Cloud Storageの最新スクレイピングデータをFirestoreに同期するスクリプト
- Cloud Storageから最新の価格データを取得
- Firestoreのkaitori_pricesコレクションを更新
- 履歴データも保存
"""

import json
import logging
import os
from datetime import datetime, timedelta

from google.cloud import firestore, storage
from google.oauth2 import service_account

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def sync_cloud_storage_to_firestore():
    """Cloud Storageの最新データをFirestoreに同期"""
    try:
        # 認証情報の設定
        credentials = service_account.Credentials.from_service_account_file('key.json')
        
        # Firestoreクライアントの初期化
        db = firestore.Client(credentials=credentials)
        
        # Cloud Storageクライアントの初期化
        storage_client = storage.Client(credentials=credentials)
        
        # バケット名の取得
        bucket_name = os.getenv('BUCKET_NAME', 'price-comparison-app-data')
        bucket = storage_client.bucket(bucket_name)
        
        # 現在の日付のパスを生成
        current_date = datetime.now().strftime('%Y/%m/%d')
        kaitori_blob = bucket.blob(f'prices/{current_date}/prices.json')
        
        if not kaitori_blob.exists():
            logger.error(f"No kaitori prices found for date: {current_date}")
            return
        
        # Cloud Storageからデータを取得
        kaitori_data = json.loads(kaitori_blob.download_as_string())
        logger.info(f"Retrieved {len(kaitori_data)} items from Cloud Storage")
        
        # 既存のkaitori_pricesコレクションをクリア
        docs = db.collection('kaitori_prices').stream()
        for doc in docs:
            doc.reference.delete()
        logger.info("Cleared existing kaitori_prices collection")
        
        # 容量ごとにデータを集計してFirestoreに保存
        series_capacity_map = {}
        
        for item in kaitori_data:
            series = item.get('series')
            capacity = item.get('capacity')
            kaitori_price_min = item.get('kaitori_price_min', 0)
            kaitori_price_max = item.get('kaitori_price_max', 0)
            colors = item.get('colors', [])
            
            if not series or not capacity:
                continue
            
            # 容量の正規化: 1GB → 1TB
            normalized_capacity = capacity
            if capacity == "1GB":
                normalized_capacity = "1TB"
                logger.info(f"Normalized capacity from 1GB to 1TB for {series}")
            
            key = f"{series}_{normalized_capacity}"
            if key not in series_capacity_map:
                series_capacity_map[key] = {
                    'series': series,
                    'capacity': normalized_capacity,
                    'kaitori_price_min': float('inf'),
                    'kaitori_price_max': 0,
                    'colors': {},
                    'source': 'kaitori-rudea',
                    'updated_at': datetime.now().isoformat()
                }
            
            # 最小・最大価格を更新
            if kaitori_price_min < series_capacity_map[key]['kaitori_price_min']:
                series_capacity_map[key]['kaitori_price_min'] = kaitori_price_min
            if kaitori_price_max > series_capacity_map[key]['kaitori_price_max']:
                series_capacity_map[key]['kaitori_price_max'] = kaitori_price_max
            
            # 色ごとの価格を保存
            for color in colors:
                series_capacity_map[key]['colors'][color] = kaitori_price_min
        
        # Firestoreに保存
        for key, data in series_capacity_map.items():
            if data['kaitori_price_min'] == float('inf'):
                data['kaitori_price_min'] = 0
            
            doc_ref = db.collection('kaitori_prices').document()
            doc_ref.set(data)
            logger.info(f"Saved to Firestore: {data['series']} {data['capacity']} - min: {data['kaitori_price_min']}, max: {data['kaitori_price_max']}")
        
        # 履歴データも保存（price_historyコレクション）
        current_timestamp = int(datetime.now().timestamp())
        for key, data in series_capacity_map.items():
            if data['kaitori_price_min'] == float('inf'):
                continue
                
            history_data = {
                'model': key,
                'timestamp': current_timestamp,
                'series': data['series'],
                'capacity': data['capacity'],
                'colors': data['colors'],
                'kaitori_price_min': data['kaitori_price_min'],
                'kaitori_price_max': data['kaitori_price_max'],
                'source': data['source'],
                'date': datetime.now().strftime('%Y-%m-%d'),
                'expiration_time': int((datetime.now() + timedelta(days=14)).timestamp())
            }
            
            doc_ref = db.collection('price_history').document()
            doc_ref.set(history_data)
            logger.info(f"Saved history: {key}")
        
        logger.info(f"Successfully synced {len(series_capacity_map)} items to Firestore")
        
        # 古い履歴データのクリーンアップ（2週間以上前）
        cleanup_old_history_data(db)
        
    except Exception as e:
        logger.error(f"Error syncing data: {str(e)}")
        raise

def cleanup_old_history_data(db):
    """2週間以上古い履歴データを削除"""
    try:
        # 2週間前のタイムスタンプ
        cutoff_timestamp = int((datetime.now() - timedelta(days=14)).timestamp())
        
        # 古いデータを検索
        query = (
            db.collection('price_history')
            .where('timestamp', '<', cutoff_timestamp)
        )
        
        docs = query.stream()
        deleted_count = 0
        
        # 古いデータを削除
        for doc in docs:
            doc.reference.delete()
            deleted_count += 1
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old price history records")
        else:
            logger.info("No old price history records to clean up")
            
    except Exception as e:
        logger.error(f"Error cleaning up old history data: {str(e)}")
        # クリーンアップの失敗は他の処理に影響を与えない
        pass

if __name__ == "__main__":
    sync_cloud_storage_to_firestore() 