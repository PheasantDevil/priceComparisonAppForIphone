import json
import logging
import os
from datetime import datetime

import boto3

# ログ設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# DynamoDBクライアントの初期化
dynamodb = boto3.resource('dynamodb')
kaitori_table = dynamodb.Table(os.environ['KAITORI_TABLE'])
official_table = dynamodb.Table(os.environ['OFFICIAL_TABLE'])
history_table = dynamodb.Table(os.environ['HISTORY_TABLE'])

def verify_table_health(table):
    """テーブルの健全性を確認"""
    try:
        response = table.describe_table()
        return response['Table']['TableStatus'] == 'ACTIVE'
    except Exception as e:
        logger.error(f"テーブル健全性確認エラー: {str(e)}")
        return False

def backup_table_data(table):
    """テーブルデータのバックアップを作成"""
    try:
        items = table.scan()['Items']
        timestamp = datetime.now().isoformat()
        
        # バックアップデータを保存
        backup_table = dynamodb.Table(f"{table.name}_backup")
        with backup_table.batch_writer() as batch:
            for item in items:
                item['backup_timestamp'] = timestamp
                batch.put_item(Item=item)
        
        return True
    except Exception as e:
        logger.error(f"バックアップ作成エラー: {str(e)}")
        return False

def restore_table_data(table):
    """バックアップからテーブルデータを復元"""
    try:
        backup_table = dynamodb.Table(f"{table.name}_backup")
        items = backup_table.scan()['Items']
        
        with table.batch_writer() as batch:
            for item in items:
                # バックアップタイムスタンプを削除
                item.pop('backup_timestamp', None)
                batch.put_item(Item=item)
        
        return True
    except Exception as e:
        logger.error(f"データ復元エラー: {str(e)}")
        return False

def lambda_handler(event, context):
    """DRハンドラーのメイン関数"""
    try:
        logger.info("DRハンドラーを開始")
        
        # テーブルの健全性確認
        tables_healthy = all([
            verify_table_health(kaitori_table),
            verify_table_health(official_table),
            verify_table_health(history_table)
        ])
        
        if not tables_healthy:
            logger.error("一部のテーブルが不健全な状態です")
            return {
                'statusCode': 500,
                'body': json.dumps('テーブルの健全性確認に失敗しました')
            }
        
        # バックアップの作成
        backup_success = all([
            backup_table_data(kaitori_table),
            backup_table_data(official_table),
            backup_table_data(history_table)
        ])
        
        if not backup_success:
            logger.error("バックアップの作成に失敗しました")
            return {
                'statusCode': 500,
                'body': json.dumps('バックアップの作成に失敗しました')
            }
        
        # テスト用のデータ復元（本番環境では条件付きで実行）
        if os.environ.get('ENVIRONMENT') == 'test':
            restore_success = all([
                restore_table_data(kaitori_table),
                restore_table_data(official_table),
                restore_table_data(history_table)
            ])
            
            if not restore_success:
                logger.error("データの復元に失敗しました")
                return {
                    'statusCode': 500,
                    'body': json.dumps('データの復元に失敗しました')
                }
        
        logger.info("DRハンドラーが正常に完了")
        return {
            'statusCode': 200,
            'body': json.dumps('DRハンドラーが正常に完了しました')
        }
        
    except Exception as e:
        logger.error(f"予期せぬエラー: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'予期せぬエラーが発生しました: {str(e)}')
        } 