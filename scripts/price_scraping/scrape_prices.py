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
        
        # 各モデルの有効な容量を定義
        self.valid_capacities = {
            "iPhone 16": ["128GB", "256GB", "512GB"],
            "iPhone 16 Plus": ["128GB", "256GB", "512GB"],
            "iPhone 16 Pro": ["128GB", "256GB", "512GB", "1TB"],
            "iPhone 16 Pro Max": ["256GB", "512GB", "1TB"],
            "iPhone 16 e": ["128GB", "256GB", "512GB"]
        }

    def _load_config(self) -> dict:
        """設定ファイルの読み込み"""
        try:
            config_path = Path(__file__).parent.parent.parent / 'config' / 'config.production.yaml'
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            error_msg = f"設定ファイルの読み込みに失敗: {e}"
            logger.error(error_msg)
            self._send_error_notification('config', error_msg)
            raise

    def _send_error_notification(self, error_type: str, error_message: str) -> None:
        """エラー通知の送信"""
        try:
            script_path = Path(__file__).parent / 'send_error_notification.py'
            subprocess.run([
                sys.executable,
                str(script_path),
                error_type,
                error_message
            ], check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"エラー通知の送信に失敗: {e}")
        except Exception as e:
            logger.error(f"エラー通知処理中に予期せぬエラー: {e}")

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
    async def scrape_url(self, url: str) -> List[Dict]:
        """指定されたURLから価格データをスクレイピング"""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            try:
                await page.goto(url, wait_until='networkidle')
                
                # 価格情報を含む要素を取得
                items = await page.query_selector_all(".tr")
                if not items:
                    error_msg = f"価格要素が見つかりません (URL: {url})"
                    logger.error(error_msg)
                    self._send_error_notification('scraping', error_msg)
                    raise ValueError(error_msg)

                results = []
                current_series = None
                current_capacity = None
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
                        elif "Plus" in model_name:
                            series = "iPhone 16 Plus"
                        elif "16 e" in model_name or "16e" in model_name:
                            series = "iPhone 16 e"
                        elif "16" in model_name:
                            series = "iPhone 16"
                        else:
                            logger.warning(f"未知のモデル名: {model_name}")
                            continue

                        # 容量を抽出
                        capacity_match = re.search(r"(\d+)(GB|TB)", model_name)
                        if not capacity_match:
                            logger.warning(f"容量が見つかりません: {model_name}")
                            continue
                        capacity = capacity_match.group(0)  # "128GB" or "1TB"

                        # 容量の組み合わせを検証
                        if not self._is_valid_capacity(series, capacity):
                            continue

                        # 新しいシリーズまたは容量の場合、前のデータを保存
                        if (current_series and current_series != series) or \
                           (current_capacity and current_capacity != capacity):
                            if product_details["colors"]:
                                result = {
                                    "id": f"{current_series}_{current_capacity}",
                                    "series": current_series,
                                    "capacity": current_capacity,
                                    **product_details
                                }
                                results.append(result)
                                product_details = {
                                    "colors": {},
                                    "kaitori_price_min": None,
                                    "kaitori_price_max": None,
                                }

                        current_series = series
                        current_capacity = capacity

                        # 価格を取得
                        price_element = await item.query_selector(".td.td2 .td2wrap")
                        price_text = await price_element.inner_text() if price_element else ""
                        price_text = price_text.strip()

                        if not price_text or "円" not in price_text:
                            logger.warning(f"価格が見つかりません: {model_name}")
                            continue

                        # カラーを抽出
                        color_match = re.search(r"(黒|白|桃|緑|青|金|灰)", model_name)
                        color = color_match.group(1) if color_match else "不明"

                        # 価格を数値に変換
                        price_value = self._price_text_to_int(price_text)
                        if price_value == 0:
                            logger.warning(f"無効な価格: {price_text} ({model_name})")
                            continue

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
                        error_msg = f"要素の処理中にエラー (URL: {url}): {e}"
                        logger.error(error_msg)
                        self._send_error_notification('scraping', error_msg)
                        continue

                # 最後のデータを保存
                if product_details["colors"]:
                    result = {
                        "id": f"{current_series}_{current_capacity}",
                        "series": current_series,
                        "capacity": current_capacity,
                        **product_details
                    }
                    results.append(result)

                if not results:
                    error_msg = f"有効な価格データが見つかりません (URL: {url})"
                    logger.error(error_msg)
                    self._send_error_notification('scraping', error_msg)
                    raise ValueError(error_msg)

                logger.info(f"スクレイピング成功 (URL: {url}): {json.dumps(results, ensure_ascii=False)}")
                return results

            except Exception as e:
                error_msg = f"スクレイピングエラー (URL: {url}): {e}"
                logger.error(error_msg)
                self._send_error_notification('scraping', error_msg)
                raise
            finally:
                await browser.close()

    async def scrape_all_prices(self) -> List[Dict]:
        """全てのURLから価格データを並行してスクレイピング"""
        tasks = []
        for url in self.config['scraper']['kaitori_rudea_urls']:
            tasks.append(self.scrape_url(url))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 結果を平坦化
        flattened_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"スクレイピング失敗: {result}")
                continue
            if isinstance(result, list):
                flattened_results.extend(result)
            else:
                flattened_results.append(result)
        
        return flattened_results

    def save_to_dynamodb(self, data: Dict) -> None:
        """DynamoDBにデータを保存"""
        try:
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
            self.kaitori_table.put_item(Item=kaitori_item)
            logger.info(f"kaitori_pricesテーブルに保存: {json.dumps(kaitori_item, ensure_ascii=False)}")
            
            # price_historyテーブルへの保存（履歴追加）
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
            self.history_table.put_item(Item=history_item)
            logger.info(f"price_historyテーブルに保存: {json.dumps(history_item, ensure_ascii=False)}")
            
        except Exception as e:
            error_msg = f"DynamoDB保存エラー: {e}"
            logger.error(error_msg)
            self._send_error_notification('dynamodb', error_msg)
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
            self._send_error_notification('dynamodb', error_msg)
            # 削除処理の失敗は他の処理に影響を与えない
            pass

    def _is_valid_capacity(self, series: str, capacity: str) -> bool:
        """指定されたモデルと容量の組み合わせが有効かどうかを検証"""
        valid_capacities = self.valid_capacities.get(series, [])
        is_valid = capacity in valid_capacities
        if not is_valid:
            logger.warning(f"無効な容量の組み合わせ: {series} {capacity} (有効な容量: {valid_capacities})")
        return is_valid

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
        error_msg = f"予期せぬエラー: {e}"
        logger.error(error_msg)
        scraper._send_error_notification('unexpected', error_msg)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 