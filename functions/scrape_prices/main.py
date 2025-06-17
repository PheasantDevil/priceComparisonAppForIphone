import json
import logging
import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from google.cloud import storage
from playwright.sync_api import sync_playwright
from tenacity import retry, stop_after_attempt, wait_exponential

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PriceScraper:
    def __init__(self):
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
    def scrape_url(self, url: str) -> List[Dict]:
        """指定されたURLから価格データをスクレイピング"""
        try:
            with sync_playwright() as p:
                # Cloud Functions環境用の設定
                browser = p.chromium.launch(
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-accelerated-2d-canvas',
                        '--disable-gpu'
                    ]
                )
                page = browser.new_page()
                
                try:
                    # ページの読み込み
                    page.goto(url, wait_until='networkidle', timeout=60000)
                    
                    # デバッグ情報の出力
                    logger.debug(f"ページのタイトル: {page.title()}")
                    logger.debug(f"URL: {page.url}")
                    
                    # 価格要素の取得
                    price_elements = page.query_selector_all('.tr')
                    if not price_elements:
                        logger.warning(f"価格要素が見つかりません: {url}")
                        return []
                    
                    logger.info(f"価格要素が{len(price_elements)}個見つかりました")
                    
                    results = []
                    for element in price_elements:
                        try:
                            # モデル名の取得
                            model_name = element.query_selector('.ttl h2')
                            if not model_name:
                                continue
                            model_text = model_name.text_content()
                            if not model_text:
                                continue
                            
                            logger.debug(f"モデル名: {model_text}")
                            
                            # モデルシリーズの識別
                            series = self._identify_model_series(model_text.strip())
                            if not series:
                                logger.warning(f"未知のモデル名: {model_text}")
                                continue
                            
                            # 容量の取得
                            capacity_match = re.search(r'(\d+)\s*[GT]B', model_text)
                            if not capacity_match:
                                logger.warning(f"容量が見つかりません: {model_text}")
                                continue
                            capacity = f"{capacity_match.group(1)}GB"
                            
                            logger.debug(f"容量: {capacity}")
                            
                            # 価格の取得
                            price_element = element.query_selector('.td.td2 .td2wrap')
                            if not price_element:
                                continue
                            price_text = price_element.text_content()
                            if not price_text:
                                continue
                            
                            # 価格の正規化
                            price = self._normalize_price(price_text.strip())
                            if not price:
                                logger.warning(f"無効な価格: {price_text}")
                                continue
                            
                            logger.debug(f"価格: {price}")
                            
                            # 色の取得
                            color_match = re.search(r'(黒|白|桃|緑|青|金|灰)', model_text)
                            color = color_match.group(1) if color_match else "不明"
                            
                            # 結果の追加
                            result = {
                                "id": f"{series}_{capacity}",
                                "series": series,
                                "capacity": capacity,
                                "colors": [color.strip()],
                                "kaitori_price_min": price,
                                "kaitori_price_max": price,
                                "updated_at": datetime.now().isoformat()
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
                    page.close()
                    browser.close()
                    
        except Exception as e:
            logger.error(f"スクレイピングエラー (URL: {url}): {e}")
            return []

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

    def _identify_model_series(self, model_name: str) -> Optional[str]:
        """モデル名からシリーズを特定"""
        model_name = model_name.strip()
        for series, pattern in self.model_patterns.items():
            if re.search(pattern, model_name, re.IGNORECASE):
                return series
        return None

    def save_to_storage(self, data: List[Dict]) -> None:
        """Cloud Storageにデータを保存"""
        try:
            # Cloud Storageクライアントの初期化
            storage_client = storage.Client()
            bucket = storage_client.bucket(os.environ.get('BUCKET_NAME'))
            
            # 現在の日時を取得
            current_time = datetime.now()
            
            # 価格データの保存
            price_blob = bucket.blob(f'prices/{current_time.strftime("%Y/%m/%d")}/prices.json')
            price_blob.upload_from_string(
                json.dumps(data, ensure_ascii=False),
                content_type='application/json'
            )
            
            # 履歴データの保存
            history_blob = bucket.blob(f'history/{current_time.strftime("%Y/%m/%d")}/history.json')
            history_data = {
                'timestamp': current_time.isoformat(),
                'prices': data
            }
            history_blob.upload_from_string(
                json.dumps(history_data, ensure_ascii=False),
                content_type='application/json'
            )
            
            logger.info(f"データをCloud Storageに保存しました: {len(data)}件")
            
        except Exception as e:
            error_msg = f"Cloud Storage保存エラー: {e}"
            logger.error(error_msg)
            raise

def scrape_prices(request):
    """Cloud Function to scrape iPhone prices."""
    try:
        # スクレイパーの初期化
        scraper = PriceScraper()
        
        # スクレイピング対象のURLリスト
        urls = [
            "https://www.rudea.jp/kaitori/iphone/",
            # 他のURLを追加
        ]
        
        # 各URLからデータをスクレイピング
        all_results = []
        for url in urls:
            results = scraper.scrape_url(url)
            all_results.extend(results)
        
        # 結果をCloud Storageに保存
        if all_results:
            scraper.save_to_storage(all_results)
            return {"status": "success", "message": f"Price scraping completed successfully. Scraped {len(all_results)} items."}
        else:
            return {"status": "warning", "message": "No price data was scraped."}
        
    except Exception as e:
        logger.error(f"Error during price scraping: {str(e)}")
        return {"status": "error", "message": str(e)} 