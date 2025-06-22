#!/usr/bin/env python3
"""
価格履歴管理スクリプト
- 価格履歴の保存
- 古いデータの自動削除
- グラフ用データの取得
"""

import json
import logging
from datetime import datetime, timedelta

from google.cloud import firestore
from google.oauth2 import service_account

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PriceHistoryManager:
    def __init__(self):
        credentials = service_account.Credentials.from_service_account_file('key.json')
        self.db = firestore.Client(credentials=credentials)
        
    def save_price_history(self, series, capacity, kaitori_price_min, kaitori_price_max, colors):
        """
        価格履歴を保存
        
        Args:
            series: iPhoneシリーズ名
            capacity: 容量
            kaitori_price_min: 最小買取価格
            kaitori_price_max: 最大買取価格
            colors: 色別価格
        """
        try:
            # 現在のタイムスタンプ
            current_timestamp = int(datetime.now().timestamp())
            
            # 2週間後の削除予定日
            expiration_time = int((datetime.now() + timedelta(days=14)).timestamp())
            
            # 履歴データを作成
            history_data = {
                'series': series,
                'capacity': capacity,
                'kaitori_price_min': kaitori_price_min,
                'kaitori_price_max': kaitori_price_max,
                'colors': colors,
                'timestamp': current_timestamp,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'expiration_time': expiration_time,
                'source': 'kaitori-rudea'
            }
            
            # Firestoreに保存
            doc_ref = self.db.collection('price_history').document()
            doc_ref.set(history_data)
            
            logger.info(f"Saved price history: {series} {capacity} - min: {kaitori_price_min}, max: {kaitori_price_max}")
            
        except Exception as e:
            logger.error(f"Error saving price history: {str(e)}")
            raise
    
    def get_price_history_for_graph(self, series, capacity, days=14):
        """
        グラフ表示用の価格履歴を取得
        
        Args:
            series: iPhoneシリーズ名
            capacity: 容量
            days: 取得する日数（デフォルト14日）
            
        Returns:
            グラフ用のデータ配列
        """
        try:
            # 指定日数前のタイムスタンプ
            start_timestamp = int((datetime.now() - timedelta(days=days)).timestamp())
            
            # クエリ実行（インデックスを避けるため、シンプルなクエリに変更）
            query = (
                self.db.collection('price_history')
                .filter('series', '==', series)
                .filter('capacity', '==', capacity)
            )
            
            docs = query.stream()
            
            # グラフ用データに変換（クライアント側でフィルタリング）
            graph_data = []
            for doc in docs:
                data = doc.to_dict()
                timestamp = data.get('timestamp', 0)
                
                # 指定日数以内のデータのみをフィルタリング
                if timestamp >= start_timestamp:
                    # dateフィールドが存在しない場合はtimestampから生成
                    date_str = data.get('date')
                    if not date_str and timestamp:
                        from datetime import datetime
                        date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
                    
                    graph_data.append({
                        'date': date_str or 'Unknown',
                        'timestamp': timestamp,
                        'price_min': data['kaitori_price_min'],
                        'price_max': data['kaitori_price_max'],
                        'price_avg': (data['kaitori_price_min'] + data['kaitori_price_max']) // 2
                    })
            
            # タイムスタンプでソート
            graph_data.sort(key=lambda x: x['timestamp'])
            
            logger.info(f"Retrieved {len(graph_data)} price history records for {series} {capacity}")
            return graph_data
            
        except Exception as e:
            logger.error(f"Error getting price history: {str(e)}")
            return []
    
    def cleanup_old_data(self):
        """
        2週間以上古いデータを削除
        """
        try:
            # 2週間前のタイムスタンプ
            cutoff_timestamp = int((datetime.now() - timedelta(days=14)).timestamp())
            
            # 古いデータを検索
            query = (
                self.db.collection('price_history')
                .filter('timestamp', '<', cutoff_timestamp)
            )
            
            docs = query.stream()
            deleted_count = 0
            
            # 古いデータを削除
            for doc in docs:
                doc.reference.delete()
                deleted_count += 1
            
            logger.info(f"Deleted {deleted_count} old price history records")
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {str(e)}")
    
    def save_all_current_prices(self):
        """
        現在の買取価格をすべて履歴に保存
        """
        try:
            # 現在の買取価格を取得
            kaitori_docs = self.db.collection('kaitori_prices').stream()
            
            saved_count = 0
            for doc in kaitori_docs:
                data = doc.to_dict()
                series = data.get('series')
                capacity = data.get('capacity')
                kaitori_price_min = data.get('kaitori_price_min', 0)
                kaitori_price_max = data.get('kaitori_price_max', 0)
                colors = data.get('colors', {})
                
                if series and capacity and kaitori_price_min > 0:
                    self.save_price_history(
                        series, capacity, kaitori_price_min, kaitori_price_max, colors
                    )
                    saved_count += 1
            
            logger.info(f"Saved {saved_count} price history records")
            
        except Exception as e:
            logger.error(f"Error saving all current prices: {str(e)}")
            raise

def main():
    """メイン処理"""
    manager = PriceHistoryManager()
    
    # 現在の価格を履歴に保存
    print("Saving current prices to history...")
    manager.save_all_current_prices()
    
    # 古いデータをクリーンアップ
    print("Cleaning up old data...")
    manager.cleanup_old_data()
    
    # サンプルでグラフデータを取得
    print("Getting sample graph data...")
    graph_data = manager.get_price_history_for_graph('iPhone 16 Pro', '1TB', days=7)
    print(f"Sample graph data: {json.dumps(graph_data, indent=2)}")

if __name__ == "__main__":
    main() 