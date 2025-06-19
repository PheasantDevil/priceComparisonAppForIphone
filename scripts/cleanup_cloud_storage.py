#!/usr/bin/env python3
"""
Cloud Storageの古いファイルを自動削除するスクリプト
- 14日以上古い価格データファイルを削除
- ストレージコストを削減
"""

import logging
import os
from datetime import datetime, timedelta

from google.cloud import storage
from google.oauth2 import service_account

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def cleanup_old_cloud_storage_files():
    """Cloud Storageの古いファイルを削除"""
    try:
        # 認証情報の設定
        credentials = service_account.Credentials.from_service_account_file('key.json')
        
        # Cloud Storageクライアントの初期化
        storage_client = storage.Client(credentials=credentials)
        
        # バケット名の取得
        bucket_name = os.getenv('BUCKET_NAME', 'price-comparison-app-data')
        bucket = storage_client.bucket(bucket_name)
        
        # 14日前の日付を計算
        cutoff_date = datetime.now() - timedelta(days=14)
        cutoff_date_str = cutoff_date.strftime('%Y/%m/%d')
        
        logger.info(f"Cleaning up files older than: {cutoff_date_str}")
        
        deleted_count = 0
        total_size_deleted = 0
        
        # 価格データディレクトリの古いファイルを削除
        blobs = bucket.list_blobs(prefix='prices/')
        
        for blob in blobs:
            # ファイルパスから日付を抽出 (prices/2024/01/15/prices.json)
            path_parts = blob.name.split('/')
            if len(path_parts) >= 4 and path_parts[0] == 'prices':
                try:
                    file_date_str = f"{path_parts[1]}/{path_parts[2]}/{path_parts[3]}"
                    file_date = datetime.strptime(file_date_str, '%Y/%m/%d')
                    
                    if file_date < cutoff_date:
                        size = blob.size
                        blob.delete()
                        deleted_count += 1
                        total_size_deleted += size
                        logger.info(f"Deleted old file: {blob.name} (size: {size} bytes)")
                        
                except (ValueError, IndexError) as e:
                    logger.warning(f"Could not parse date from path: {blob.name}, error: {e}")
                    continue
        
        # 設定ファイルの古いバックアップも削除
        config_blobs = bucket.list_blobs(prefix='config/backup/')
        for blob in config_blobs:
            # ファイルの作成日時を確認
            if blob.time_created < cutoff_date:
                size = blob.size
                blob.delete()
                deleted_count += 1
                total_size_deleted += size
                logger.info(f"Deleted old config backup: {blob.name} (size: {size} bytes)")
        
        logger.info(f"Cleanup completed. Deleted {deleted_count} files, total size: {total_size_deleted} bytes")
        
        # ストレージクラスを最適化（コスト削減）
        optimize_storage_class(bucket)
        
    except Exception as e:
        logger.error(f"Error during Cloud Storage cleanup: {str(e)}")
        raise

def optimize_storage_class(bucket):
    """ストレージクラスを最適化してコストを削減"""
    try:
        # 7日以上古いファイルをNearlineに移動
        nearline_cutoff = datetime.now() - timedelta(days=7)
        
        blobs = bucket.list_blobs(prefix='prices/')
        optimized_count = 0
        
        for blob in blobs:
            path_parts = blob.name.split('/')
            if len(path_parts) >= 4 and path_parts[0] == 'prices':
                try:
                    file_date_str = f"{path_parts[1]}/{path_parts[2]}/{path_parts[3]}"
                    file_date = datetime.strptime(file_date_str, '%Y/%m/%d')
                    
                    # 7日以上古く、まだStandardクラスのファイルをNearlineに移動
                    if (file_date < nearline_cutoff and 
                        blob.storage_class == 'STANDARD'):
                        
                        # 新しいNearlineオブジェクトを作成
                        new_blob = bucket.copy_blob(
                            blob, bucket, blob.name,
                            storage_class='NEARLINE'
                        )
                        
                        # 古いStandardオブジェクトを削除
                        blob.delete()
                        optimized_count += 1
                        logger.info(f"Optimized storage class for: {blob.name}")
                        
                except (ValueError, IndexError) as e:
                    continue
        
        if optimized_count > 0:
            logger.info(f"Storage class optimization completed. Optimized {optimized_count} files")
        else:
            logger.info("No files needed storage class optimization")
            
    except Exception as e:
        logger.error(f"Error during storage class optimization: {str(e)}")
        # 最適化の失敗は他の処理に影響を与えない
        pass

if __name__ == "__main__":
    cleanup_old_cloud_storage_files() 