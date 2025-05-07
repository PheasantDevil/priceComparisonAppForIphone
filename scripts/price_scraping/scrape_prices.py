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
import sys
from datetime import datetime, timedelta
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

class PriceScraper:
    def __init__(self):
        self.config = self._load_config()
        self.dynamodb = boto3.resource('dynamodb')
        self.kaitori_table = self.dynamodb.Table('kaitori_prices')
        self.history_table = self.dynamodb.Table('price_history')

    def _load_config(self) -> dict:
        """設定ファイルの読み込み"""
        try:
            config_path = Path(__file__).parent.parent.parent / 'config' / 'config.production.yaml'
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"設定ファイルの読み込みに失敗: {e}")
            raise

    def _price_text_to_int(self, price_text: str) -> int:
        """価格テキストを整数に変換"""
        try:
            return int(price_text.replace("円", "").replace(",", ""))
        except (ValueError, AttributeError):
            return 0

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    async def scrape_url(self, url: str) -> Dict:
        """指定されたURLから価格データをスクレイピング"""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            try:
                await page.goto(url, wait_until='networkidle')
                
                # 価格情報を含む要素を取得
                items = await page.query_selector_all(".tr")
                if not items:
                    logger.warning(f"価格要素が見つかりません (URL: {url})")
                    return {}

                product_details = {
                    "colors": {},
                    "kaitori_price_min": None,
                    "kaitori_price_max": None,
                }

                for item in items:
                    try:
                        # モデル名を取得
                        model_element = await item.query_selector(".ttl h2")
                        model_name = await model_element.inner_text() if model_element else ""
                        model_name = model_name.strip()

                        # モデル名からシリーズを判定
                        if "Pro Max" in model_name:
                            series = "iPhone 16 Pro Max"
                        elif "Pro" in model_name:
                            series = "iPhone 16 Pro"
                        elif "16" in model_name:
                            series = "iPhone 16"
                        elif "16" in model_name:
                            series = "iPhone 16 e"
                        else:
                            continue

                        # 容量を抽出
                        capacity_match = re.search(r"(\d+)(GB|TB)", model_name)
                        if not capacity_match:
                            continue
                        capacity = capacity_match.group(0)  # "128GB" or "1TB"

                        # 価格を取得
                        price_element = await item.query_selector(".td.td2 .td2wrap")
                        price_text = await price_element.inner_text() if price_element else ""
                        price_text = price_text.strip()

                        if model_name and price_text and "円" in price_text:
                            # カラーを抽出
                            color_match = re.search(r"(黒|白|桃|緑|青|金|灰)", model_name)
                            color = color_match.group(1) if color_match else "不明"

                            # 価格を数値に変換
                            price_value = self._price_text_to_int(price_text)

                            # 色ごとの価格を保存
                            product_details["colors"][color] = {
                                "price_text": price_text,
                                "price_value": price_value,
                            }

                            # 最小・最大価格を更新
                            current_min = product_details["kaitori_price_min"]
                            current_max = product_details["kaitori_price_max"]

                            if current_min is None or price_value < current_min:
                                product_details["kaitori_price_min"] = price_value
                            if current_max is None or price_value > current_max:
                                product_details["kaitori_price_max"] = price_value

                    except Exception as e:
                        logger.error(f"要素の処理中にエラー (URL: {url}): {e}")
                        continue

                # 結果を整形
                result = {
                    "id": f"{series}_{capacity}",
                    "series": series,
                    "capacity": capacity,
                    **product_details
                }

                logger.info(f"スクレイピング成功 (URL: {url}): {json.dumps(result, ensure_ascii=False)}")
                return result

            except Exception as e:
                logger.error(f"スクレイピングエラー (URL: {url}): {e}")
                raise
            finally:
                await browser.close()

    async def scrape_all_prices(self) -> List[Dict]:
        """全てのURLから価格データを並行してスクレイピング"""
        tasks = []
        for url in self.config['scraper']['kaitori_rudea_urls']:
            tasks.append(self.scrape_url(url))
        return await asyncio.gather(*tasks, return_exceptions=True)

    def save_to_dynamodb(self, data: Dict) -> None:
        """DynamoDBにデータを保存"""
        try:
            # kaitori_pricesテーブルへの保存（上書き）
            self.kaitori_table.put_item(Item=data)
            
            # price_historyテーブルへの保存（履歴追加）
            history_data = {
                **data,
                'timestamp': datetime.now().isoformat()
            }
            self.history_table.put_item(Item=history_data)
            
        except Exception as e:
            logger.error(f"DynamoDB保存エラー: {e}")
            raise

    def delete_old_data(self) -> None:
        """2週間以上前のデータを削除"""
        try:
            two_weeks_ago = (datetime.now() - timedelta(days=14)).isoformat()
            
            # 2週間以上前のデータを検索
            response = self.history_table.scan(
                FilterExpression='timestamp < :two_weeks_ago',
                ExpressionAttributeValues={':two_weeks_ago': two_weeks_ago}
            )
            
            # 古いデータを削除
            with self.history_table.batch_writer() as batch:
                for item in response.get('Items', []):
                    batch.delete_item(
                        Key={
                            'id': item['id'],
                            'timestamp': item['timestamp']
                        }
                    )
                    
        except Exception as e:
            logger.error(f"古いデータの削除に失敗: {e}")
            # 削除処理の失敗は他の処理に影響を与えない
            pass

async def main():
    try:
        scraper = PriceScraper()
        
        # 価格データのスクレイピング
        results = await scraper.scrape_all_prices()
        
        # 成功した結果のみを処理
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"スクレイピング失敗: {result}")
                continue
            scraper.save_to_dynamodb(result)
        
        # 古いデータの削除
        scraper.delete_old_data()
        
    except Exception as e:
        logger.error(f"予期せぬエラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 