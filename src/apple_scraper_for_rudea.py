import json
import logging
import os
import re
from decimal import Decimal
from pathlib import Path

import boto3
import requests
import yaml
from bs4 import BeautifulSoup

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Decimalを処理するJSONエンコーダを追加
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super(DecimalEncoder, self).default(obj)

def load_config():
    try:
        config_path = Path(__file__).parent.parent / 'config' / 'config.production.yaml'
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return None

def get_official_prices(series):
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('iphone_prices')
        
        # Handle both "iPhone 16e" and "iPhone 16 e" formats
        lookup_series = series
        if series == 'iPhone 16 e':
            lookup_series = 'iPhone 16e'
            
        logger.info(f"Looking up official prices for {lookup_series} (original request: {series})")
        
        response = table.get_item(
            Key={'series': lookup_series}
        )
        
        if 'Item' in response:
            logger.info(f"Found official prices for {lookup_series}: {response['Item']}")
            # pricesマップから価格データを取得
            prices = response['Item'].get('prices', {})

            # iPhone 16eのデータ形式を他のモデルと合わせる
            if lookup_series == 'iPhone 16e':
                formatted_prices = {}
                for capacity, color_prices in prices.items():
                    # 各容量の最初の色の価格を取得（黒か白）
                    if isinstance(color_prices, dict) and len(color_prices) > 0:
                        first_color = list(color_prices.keys())[0]
                        price_value = color_prices.get(first_color)
                        if isinstance(price_value, (int, Decimal)):
                            formatted_prices[capacity] = str(int(price_value))
                        else:
                            formatted_prices[capacity] = str(price_value)
                return formatted_prices
            
            return prices
        else:
            logger.warning(f"No official prices found for {lookup_series}")
            return {}
            
    except Exception as e:
        logger.error(f"Error getting official prices: {e}")
        logger.error(f"Error details: {str(e)}")  # より詳細なエラー情報
        return {}

def get_kaitori_prices(series):
    try:
        logger.info(f"Starting price fetch for series: {series}")
        config = load_config()
        
        if not config:
            raise Exception("Failed to load configuration")

        # シリーズに対応するURLを取得
        series_url_map = {
            'iPhone 16': config['scraper']['kaitori_rudea_urls'][0],
            'iPhone 16 Pro': config['scraper']['kaitori_rudea_urls'][1],
            'iPhone 16 Pro Max': config['scraper']['kaitori_rudea_urls'][2],
            'iPhone 16 e': config['scraper']['kaitori_rudea_urls'][3],
            'iPhone 16e': config['scraper']['kaitori_rudea_urls'][3]  # Add support for both formats
        }
        
        # シリーズに対応するURLを取得する前にログ出力
        logger.info(f"Looking up URL for series: {series}, Available mappings: {list(series_url_map.keys())}")
        
        if series not in series_url_map:
            logger.warning(f"No URL configured for series: {series}")
            # エラーを返す代わりに、空のデータと公式価格のみを返す
            return {
                series: {
                    'kaitori': {},
                    'official': get_official_prices(series)
                }
            }

        url = series_url_map[series]
        headers = {'User-Agent': config['scraper']['user_agent']}
        
        logger.info(f"Fetching data from URL: {url}")
        
        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=config['scraper']['request_timeout']
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            logger.info(f"HTML content length: {len(response.text)}")
            
            # デバッグ用にHTML�造を解析
            main_content = soup.find('div', class_='main-content')
            if main_content:
                logger.info("Found main-content div")
                logger.info(f"Main content first 500 chars: {str(main_content)[:500]}")
            
            # 買取価格データを抽出
            kaitori_prices = {}
            
            # 価格情報を含む要素を探す（実際のサイトの構造に合わせて修正）
            price_elements = soup.find_all('div', class_='tr') # idは"product4898"のように最後の4桁が行ごとに違ったため使用できず
            if price_elements:
                for elem in price_elements:
                    # 容量を探す（例: "128GB"などのテキストを含む要素）
                    capacity_elem = elem.find('h2') or \
                                  elem.find('div', class_='ttl')
                    # 価格を探す
                    price_elem = elem.find('div', class_='td2wrap') or \
                               elem.find('div', class_='td td2')
                    
                    if capacity_elem and price_elem:
                        capacity_text = capacity_elem.text.strip()
                        # 容量のフォーマットを統一（GB/TB両方に対応）
                        capacity_match = re.search(r'(\d+)\s*(GB|TB)', capacity_text, re.IGNORECASE)
                        if capacity_match:
                            # 容量の数値と単位を取得
                            capacity_num = capacity_match.group(1)
                            capacity_unit = capacity_match.group(2).upper()
                            capacity = f"{capacity_num}{capacity_unit}"
                            # 価格から不要な文字を削除
                            price = re.sub(r'[^\d]', '', price_elem.text.strip())
                            kaitori_prices[capacity] = price
                            logger.info(f"Found price for {capacity}: {price}")
                        else:
                            logger.warning(f"Could not extract capacity from: {capacity_text}")
                
                if not kaitori_prices:
                    logger.warning("No valid price data found in elements")
                    logger.info(f"Found {len(price_elements)} price elements")
                    # 最初の要素の構造をログ出力
                    if price_elements:
                        logger.info(f"First price element structure: {str(price_elements[0])}")
            else:
                logger.warning("No price elements found")
                # ページ構造の確認のため、主要な要素をログ出力
                main_elements = soup.find_all('div', class_=['main', 'content', 'product-list'])
                logger.info(f"Found main elements: {[elem.get('class', []) for elem in main_elements]}")
            
            # 公式価格を取得
            official_prices = get_official_prices(series)
            
            result = {
                series: {
                    'kaitori': kaitori_prices,
                    'official': official_prices
                }
            }
            
            logger.info(f"Returning data for {series}: {json.dumps(result, indent=4, cls=DecimalEncoder)}")
            return result
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch data from URL: {e}")
            logger.error(f"Response status code: {getattr(e.response, 'status_code', 'N/A')}")
            logger.error(f"Response content: {getattr(e.response, 'text', 'N/A')[:500]}")
            return {
                series: {
                    'kaitori': {},
                    'official': get_official_prices(series)
                }
            }
            
    except Exception as e:
        logger.error(f"Error in get_kaitori_prices: {e}")
        logger.error(f"Error details: {str(e)}")
        return {
            series: {
                'kaitori': {},
                'official': get_official_prices(series)
            }
        }
