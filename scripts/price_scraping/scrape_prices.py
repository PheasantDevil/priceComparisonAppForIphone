#!/usr/bin/env python3
"""
iPhone価格スクレイピングスクリプト
- 買取価格データの取得
- DynamoDBへの保存
- 2週間経過データの削除
"""

import asyncio
import json
import logging
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional

import boto3
import yaml
from playwright.async_api import async_playwright
from tenacity import retry, stop_after_attempt, wait_exponential

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Decimalを処理するJSONエンコーダを追加
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        """
        Converts objects supporting modulo and numeric conversion to int or float for JSON encoding.
        
        If the object supports modulo operation, it is converted to an int if it represents a whole number,
        otherwise to a float. Falls back to the default JSON encoding for unsupported types.
        """
        if isinstance(obj):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super(DecimalEncoder, self).default(obj)

class PriceScraper:
    def __init__(self, config: Dict):
        self.config = config
        self.playwright = None
        self.browser = None
        self.context = None
        self.kaitori_table = boto3.resource('dynamodb').Table('kaitori_prices')
        self.history_table = boto3.resource('dynamodb').Table('price_history')
        self.official_table = boto3.resource('dynamodb').Table('official_prices')
        self.model_patterns = {
            "iPhone 16 Pro Max": r"iPhone\s*16\s*Pro\s*Max",
            "iPhone 16 Pro": r"iPhone\s*16\s*Pro(?!\s*Max)",
            "iPhone 16 Plus": r"iPhone\s*16\s*Plus",
            "iPhone 16 e": r"iPhone\s*16\s*[eE]",
            "iPhone 16": r"iPhone\s*16(?!\s*(?:Pro|Plus|[eE]))"
        }
        
        # 各モデルの有効な容量を定義
        self.valid_capacities = {
            "iPhone 16": ["128GB", "256GB", "512GB"],
            "iPhone 16 Plus": ["128GB", "256GB", "512GB"],
            "iPhone 16 Pro": ["128GB", "256GB", "512GB", "1TB"],
            "iPhone 16 Pro Max": ["256GB", "512GB", "1TB"],
            "iPhone 16 e": ["128GB", "256GB", "512GB"]
        }

    async def __aenter__(self):
        """非同期コンテキストマネージャーのエントリーポイント"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch()
        self.context = await self.browser.new_context()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャーの終了処理"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    def _price_text_to_int(self, price_text: str) -> int:
        """価格テキストを整数に変換"""
        try:
            return int(price_text.replace("円", "").replace(",", ""))
        except (ValueError, AttributeError):
            return 0

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True
    )
    async def scrape_url(self, url: str) -> List[Dict]:
        """指定されたURLから価格データをスクレイピング"""
        try:
            # ページの読み込み
            page = await self.context.new_page()
            try:
                await page.goto(url, wait_until='networkidle', timeout=60000)
                
                # デバッグ情報の出力
                logger.debug(f"ページのタイトル: {await page.title()}")
                logger.debug(f"URL: {page.url}")
                
                # 価格要素の取得（セレクターを修正）
                price_elements = await page.query_selector_all('.tr')
                if not price_elements:
                    logger.warning(f"価格要素が見つかりません: {url}")
                    # ページ構造のデバッグ
                    content = await page.content()
                    logger.debug(f"ページ構造: {content[:500]}...")  # 最初の500文字のみ表示
                    return []
                
                logger.info(f"価格要素が{len(price_elements)}個見つかりました")
                
                results = []
                for element in price_elements:
                    try:
                        # モデル名の取得（セレクターを修正）
                        model_name = await element.query_selector('.ttl h2')
                        if not model_name:
                            continue
                        model_text = await model_name.text_content()
                        if not model_text:
                            continue
                        
                        logger.debug(f"モデル名: {model_text}")
                        
                        # モデルシリーズの識別
                        series = self._identify_model_series(model_text.strip())
                        if not series:
                            logger.warning(f"未知のモデル名: {model_text}")
                            continue
                        
                        # 容量の取得（正規表現で抽出）
                        capacity_match = re.search(r'(\d+)\s*[GT]B', model_text)
                        if not capacity_match:
                            logger.warning(f"容量が見つかりません: {model_text}")
                            continue
                        capacity = f"{capacity_match.group(1)}GB"
                        
                        logger.debug(f"容量: {capacity}")
                        
                        # 価格の取得（セレクターを修正）
                        price_element = await element.query_selector('.td.td2 .td2wrap')
                        if not price_element:
                            continue
                        price_text = await price_element.text_content()
                        if not price_text:
                            continue
                        
                        # 価格の正規化
                        price = self._normalize_price(price_text.strip())
                        if not price:
                            logger.warning(f"無効な価格: {price_text}")
                            continue
                        
                        logger.debug(f"価格: {price}")
                        
                        # 色の取得（正規表現で抽出）
                        color_match = re.search(r'(黒|白|桃|緑|青|金|灰)', model_text)
                        color = color_match.group(1) if color_match else "不明"
                        
                        # 結果の追加
                        result = {
                            "id": f"{series}_{capacity}",
                            "series": series,
                            "capacity": capacity,
                            "colors": [color.strip()],
                            "kaitori_price_min": price,
                            "kaitori_price_max": price
                        }
                        
                        logger.debug(f"結果: {json.dumps(result, ensure_ascii=False)}")
                        results.append(result)
                        
                    except Exception as e:
                        logger.error(f"要素の処理中にエラーが発生: {e}")
                        continue
                
                if results:
                    logger.info(f"{len(results)}件の価格データを取得しました: {url}")
                
                return results
                
            finally:
                await page.close()
                
        except Exception as e:
            logger.error(f"スクレイピングエラー (URL: {url}): {e}")
            return []

    def _normalize_capacity(self, capacity: str) -> Optional[str]:
        """容量を正規化"""
        try:
            # 数値の抽出
            match = re.search(r'(\d+)\s*[Gg][Bb]', capacity)
            if not match:
                return None
            return f"{match.group(1)}GB"
        except Exception:
            return None

    def _normalize_price(self, price: str) -> Optional[int]:
        """価格を正規化"""
        try:
            # 数値の抽出
            match = re.search(r'(\d+(?:,\d+)*)', price)
            if not match:
                return None
            # カンマを除去して整数に変換
            return int(match.group(1).replace(',', ''))
        except Exception:
            return None

    async def scrape_all_prices(self) -> List[Dict]:
        """全てのURLから価格データを並行してスクレイピング"""
        if not self.context:
            raise RuntimeError("ブラウザコンテキストが初期化されていません")

        # 並列処理の設定
        semaphore = asyncio.Semaphore(3)  # 同時実行数を制限
        
        async def scrape_with_semaphore(url: str) -> List[Dict]:
            async with semaphore:
                try:
                    return await self.scrape_url(url)
                except Exception as e:
                    logger.error(f"スクレイピング失敗 (URL: {url}): {e}")
                    return []

        # タスクの作成と実行
        tasks = [scrape_with_semaphore(url) for url in self.config['scraper']['kaitori_rudea_urls']]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 結果の処理
        flattened_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"スクレイピング失敗: {result}")
                continue
            if isinstance(result, list):
                flattened_results.extend(result)
            else:
                flattened_results.append(result)
        
        # 結果の検証
        if not flattened_results:
            logger.warning("有効な価格データが見つかりませんでした")
        else:
            logger.info(f"合計{len(flattened_results)}件の価格データを取得しました")
        
        return flattened_results

    def save_to_dynamodb(self, data: Dict) -> None:
        """DynamoDBにデータを保存"""
        try:
            # バッチ書き込みの準備
            with self.kaitori_table.batch_writer() as batch:
                # kaitori_pricesテーブルへの保存（上書き）
                kaitori_item = {
                    "id": data["id"],
                    "series": data["series"],
                    "capacity": data["capacity"],
                    "colors": data["colors"],
                    "kaitori_price_min": data["kaitori_price_min"],
                    "kaitori_price_max": data["kaitori_price_max"],
                    "updated_at": datetime.now().isoformat()
                }
                batch.put_item(Item=kaitori_item)
                logger.info(f"kaitori_pricesテーブルに保存: {json.dumps(kaitori_item, ensure_ascii=False)}")
            
            # price_historyテーブルへの保存（履歴追加）
            with self.history_table.batch_writer() as batch:
                current_timestamp = int(datetime.now().timestamp())
                history_item = {
                    "model": data["id"],
                    "timestamp": current_timestamp,
                    "series": data["series"],
                    "capacity": data["capacity"],
                    "colors": data["colors"],
                    "kaitori_price_min": data["kaitori_price_min"],
                    "kaitori_price_max": data["kaitori_price_max"],
                    "expiration_time": int((datetime.now() + timedelta(days=14)).timestamp())
                }
                batch.put_item(Item=history_item)
                logger.info(f"price_historyテーブルに保存: {json.dumps(history_item, ensure_ascii=False)}")
            
        except Exception as e:
            error_msg = f"DynamoDB保存エラー: {e}"
            logger.error(error_msg)
            raise

    def delete_old_data(self) -> None:
        """2週間以上前のデータを削除"""
        try:
            two_weeks_ago = int((datetime.now() - timedelta(days=14)).timestamp())
            
            # 2週間以上前のデータを検索
            response = self.history_table.scan(
                FilterExpression='#ts < :two_weeks_ago',
                ExpressionAttributeValues={':two_weeks_ago': two_weeks_ago},
                ExpressionAttributeNames={'#ts': 'timestamp'}  # 予約語の回避
            )
            
            items = response.get('Items', [])
            if not items:
                logger.info("2週間以上経過しているデータは存在しないため、削除処理をスキップしました")
                return
            
            # 古いデータを削除
            with self.history_table.batch_writer() as batch:
                for item in items:
                    batch.delete_item(
                        Key={
                            'model': item['model'],
                            'timestamp': item['timestamp']
                        }
                    )
                    logger.info(f"古いデータを削除: {json.dumps(item, ensure_ascii=False)}")
            
            logger.info(f"合計{len(items)}件の古いデータを削除しました")
                    
        except Exception as e:
            error_msg = f"古いデータの削除処理中にエラーが発生: {e}"
            logger.error(error_msg)
            # 削除処理の失敗は他の処理に影響を与えない
            pass

    def _is_valid_capacity(self, series: str, capacity: str) -> bool:
        """指定されたモデルと容量の組み合わせが有効かどうかを検証"""
        valid_capacities = self.valid_capacities.get(series, [])
        is_valid = capacity in valid_capacities
        if not is_valid:
            logger.warning(f"無効な容量の組み合わせ: {series} {capacity} (有効な容量: {valid_capacities})")
        return is_valid

    def _identify_model_series(self, model_name: str) -> Optional[str]:
        """モデル名からシリーズを特定"""
        model_name = model_name.strip()
        for series, pattern in self.model_patterns.items():
            if re.search(pattern, model_name, re.IGNORECASE):
                return series
        return None

    def get_official_prices(self, series: str) -> Dict[str, str]:
        """
        Retrieves official iPhone prices by series and capacity from DynamoDB.
        
        For the specified series, queries the official prices table for each standard capacity.
        Returns a dictionary mapping each capacity to the lowest available price among all colors.
        If no prices are found or an error occurs, returns an empty dictionary.
        
        Args:
            series: The iPhone series name to look up.
        
        Returns:
            A dictionary where keys are capacities (e.g., '128GB') and values are the lowest price as strings.
        """
        try:
            # Handle both "iPhone 16e" and "iPhone 16 e" formats
            lookup_series = series.replace(' e', 'e') if ' e' in series else series
            logger.info(f"Looking up official prices for {lookup_series} (original request: {series})")
            
            # 各容量の価格を取得
            formatted_prices = {}
            capacities = ['128GB', '256GB', '512GB', '1TB']
            
            for capacity in capacities:
                try:
                    response = self.official_table.get_item(
                        Key={
                            'series': lookup_series,
                            'capacity': capacity
                        }
                    )
                    
                    if 'Item' in response:
                        # 各色の価格から最小値を取得
                        colors = response['Item'].get('colors', {})
                        if colors:
                            min_price = min((str(price)) for price in colors.values())
                            formatted_prices[capacity] = str(min_price)
                            logger.info(f"Found price for {lookup_series} {capacity}: {min_price}")
                        else:
                            logger.warning(f"No color prices found for {lookup_series} {capacity}")
                    else:
                        logger.warning(f"No data found for {lookup_series} {capacity}")
                except Exception as e:
                    logger.error(f"Error getting price for {capacity}: {e}")
                    continue
            
            if not formatted_prices:
                logger.warning(f"No official prices found for {lookup_series}")
            else:
                logger.info(f"Found official prices for {lookup_series}: {formatted_prices}")
            return formatted_prices
                
        except Exception as e:
            logger.error(f"Error getting official prices: {e}")
            return {}

def load_config() -> dict:
    """設定ファイルの読み込み"""
    try:
        # 環境変数から設定ファイルのパスを取得
        config_path = os.getenv('CONFIG_FILE', 'config/config.production.yaml')
        config_path = Path(config_path)
        
        if not config_path.exists():
            error_msg = f"設定ファイルが見つかりません: {config_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            if not config:
                error_msg = "設定ファイルが空です"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # 必須の設定項目を確認
            if 'scraper' not in config:
                error_msg = "設定ファイルに'scraper'セクションがありません"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            if 'kaitori_rudea_urls' not in config['scraper']:
                error_msg = "設定ファイルに'kaitori_rudea_urls'が設定されていません"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            logger.info(f"設定ファイルを読み込みました: {config_path}")
            return config
    except Exception as e:
        error_msg = f"設定ファイルの読み込みに失敗: {e}"
        logger.error(error_msg)
        raise

async def main():
    """メイン処理"""
    try:
        # 設定ファイルの読み込み
        config_file = os.environ.get('CONFIG_FILE', 'config/config.production.yaml')
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        logger.info(f"設定ファイルを読み込みました: {config_file}")

        # スクレイピングの実行
        async with PriceScraper(config) as scraper:
            results = await scraper.scrape_all_prices()
            
            # 結果の保存
            for result in results:
                scraper.save_to_dynamodb(result)

            # 古いデータの削除
            scraper.delete_old_data()

    except Exception as e:
        logger.error(f"予期せぬエラーが発生しました: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 