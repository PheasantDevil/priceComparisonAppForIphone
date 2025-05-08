#!/usr/bin/env python3
"""
価格スクレイピングワークフローの手動実行テスト
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

# 相対インポートに変更
from .scrape_prices import PriceScraper
from .send_error_notification import send_notification

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_scraping():
    """スクレイピングのテスト実行"""
    try:
        logger.info("スクレイピングテストを開始します")
        scraper = PriceScraper()
        
        # スクレイピングの実行
        results = await scraper.scrape_all_prices()
        
        # 結果の検証
        if not results:
            raise Exception("スクレイピング結果が空です")
        
        # 各結果の検証
        for result in results:
            if isinstance(result, Exception):
                raise result
            
            # 必須フィールドの存在確認
            required_fields = ['id', 'series', 'capacity', 'colors', 'kaitori_price_min', 'kaitori_price_max']
            for field in required_fields:
                if field not in result:
                    raise Exception(f"結果に必須フィールド '{field}' が存在しません")
            
            # 価格の妥当性確認
            if result['kaitori_price_min'] <= 0 or result['kaitori_price_max'] <= 0:
                raise Exception(f"無効な価格が検出されました: {result['id']}")
            
            logger.info(f"シリーズ {result['series']} の {result['capacity']} のスクレイピングに成功")
        
        logger.info("スクレイピングテストが正常に完了しました")
        return True
        
    except Exception as e:
        logger.error(f"スクレイピングテストでエラーが発生しました: {str(e)}")
        return False

def test_dynamodb_operations():
    """DynamoDB操作のテスト"""
    try:
        logger.info("DynamoDB操作のテストを開始します")
        scraper = PriceScraper()
        
        # テストデータの作成
        test_data = {
            'id': f'test_{datetime.now().strftime("%Y%m%d%H%M%S")}',
            'series': 'iPhone 16 Pro',
            'capacity': '128GB',
            'colors': {
                '黒': {
                    'price_text': '123,456円',
                    'price_value': 123456
                }
            },
            'kaitori_price_min': 123456,
            'kaitori_price_max': 123456
        }
        
        # データの保存
        scraper.save_to_dynamodb(test_data)
        logger.info("テストデータの保存に成功しました")
        
        # 古いデータの削除
        scraper.delete_old_data()
        logger.info("古いデータの削除に成功しました")
        
        logger.info("DynamoDB操作のテストが正常に完了しました")
        return True
        
    except Exception as e:
        logger.error(f"DynamoDB操作のテストでエラーが発生しました: {str(e)}")
        return False

def test_error_notification():
    """エラー通知のテスト"""
    try:
        logger.info("エラー通知のテストを開始します")
        
        # テストメッセージの送信
        test_message = f"テスト通知: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        send_notification(test_message)
        
        logger.info("エラー通知のテストが正常に完了しました")
        return True
        
    except Exception as e:
        logger.error(f"エラー通知のテストでエラーが発生しました: {str(e)}")
        return False

async def main():
    """メイン処理"""
    try:
        # 環境変数の確認
        required_env_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'LINE_CHANNEL_ACCESS_TOKEN']
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        if missing_vars:
            raise Exception(f"必要な環境変数が設定されていません: {', '.join(missing_vars)}")
        
        # 各テストの実行
        scraping_success = await test_scraping()
        dynamodb_success = test_dynamodb_operations()
        notification_success = test_error_notification()
        
        # 結果の集計
        if all([scraping_success, dynamodb_success, notification_success]):
            logger.info("すべてのテストが正常に完了しました")
            return 0
        else:
            logger.error("一部のテストが失敗しました")
            return 1
            
    except Exception as e:
        logger.error(f"テスト実行中にエラーが発生しました: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main())) 