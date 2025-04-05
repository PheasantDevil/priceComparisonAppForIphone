import json
import logging
import os
import re
import traceback
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
        # Lambda環境での設定ファイルのパスを確認
        lambda_config_path = '/var/task/config/config.production.yaml'
        local_config_path = Path(__file__).parent.parent / 'config' / 'config.production.yaml'
        
        if os.path.exists(lambda_config_path):
            logger.info(f"Loading config from Lambda path: {lambda_config_path}")
            with open(lambda_config_path, 'r') as f:
                return yaml.safe_load(f)
        elif os.path.exists(local_config_path):
            logger.info(f"Loading config from local path: {local_config_path}")
            with open(local_config_path, 'r') as f:
                return yaml.safe_load(f)
        else:
            logger.error("Config file not found in either Lambda or local path")
            return None
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        logger.error(f"Current working directory: {os.getcwd()}")
        logger.error(f"Directory contents: {os.listdir()}")
        return None

def get_official_prices(series):
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('official_prices')
        
        # Handle both "iPhone 16e" and "iPhone 16 e" formats
        lookup_series = series.replace(' e', 'e') if ' e' in series else series
        logger.info(f"Looking up official prices for {lookup_series} (original request: {series})")
        
        # 各容量の価格を取得
        formatted_prices = {}
        capacities = ['128GB', '256GB', '512GB', '1TB']
        
        for capacity in capacities:
            try:
                response = table.get_item(
                    Key={
                        'series': lookup_series,
                        'capacity': capacity
                    }
                )
                
                if 'Item' in response:
                    # 各色の価格から最小値を取得
                    colors = response['Item'].get('colors', {})
                    if colors:
                        min_price = min(Decimal(str(price)) for price in colors.values())
                        formatted_prices[capacity] = str(min_price)
                        logger.info(f"Found price for {lookup_series} {capacity}: {min_price}")
                    else:
                        logger.warning(f"No color prices found for {lookup_series} {capacity}")
                else:
                    logger.warning(f"No data found for {lookup_series} {capacity}")
            except Exception as e:
                logger.error(f"Error getting price for {capacity}: {e}")
                logger.error(f"Stack trace: {traceback.format_exc()}")
                continue
        
        if not formatted_prices:
            logger.warning(f"No official prices found for {lookup_series}")
        else:
            logger.info(f"Found official prices for {lookup_series}: {formatted_prices}")
        return formatted_prices
            
    except Exception as e:
        logger.error(f"Error getting official prices: {e}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        return {}

def get_kaitori_prices(series):
    try:
        logger.info(f"Starting price fetch for series: {series}")
        config = load_config()
        
        if not config:
            logger.error("Failed to load configuration, using fallback URLs")
            # フォールバックURLを使用
            fallback_urls = {
                'iPhone 16': 'https://www.rudea.net/iphone16',
                'iPhone 16 Pro': 'https://www.rudea.net/iphone16pro',
                'iPhone 16 Pro Max': 'https://www.rudea.net/iphone16promax',
                'iPhone 16 e': 'https://www.rudea.net/iphone16e',
                'iPhone 16e': 'https://www.rudea.net/iphone16e'
            }
            series_url_map = fallback_urls
        else:
            series_url_map = {
                'iPhone 16': config['scraper']['kaitori_rudea_urls'][0],
                'iPhone 16 Pro': config['scraper']['kaitori_rudea_urls'][1],
                'iPhone 16 Pro Max': config['scraper']['kaitori_rudea_urls'][2],
                'iPhone 16 e': config['scraper']['kaitori_rudea_urls'][3],
                'iPhone 16e': config['scraper']['kaitori_rudea_urls'][3]
            }
        
        logger.info(f"Looking up URL for series: {series}, Available mappings: {list(series_url_map.keys())}")
        
        if series not in series_url_map:
            logger.warning(f"No URL configured for series: {series}")
            return {
                series: {
                    'kaitori': {},
                    'official': get_official_prices(series)
                }
            }

        url = series_url_map[series]
        headers = {
            'User-Agent': config.get('scraper', {}).get('user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        }
        timeout = config.get('scraper', {}).get('request_timeout', 10)
        
        logger.info(f"Fetching data from URL: {url} with timeout: {timeout}")
        
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            logger.info(f"HTML content length: {len(response.text)}")
            
            # デバッグ用にHTML構造を解析
            main_content = soup.find('div', class_='main-content')
            if main_content:
                logger.info("Found main-content div")
                logger.info(f"Main content structure: {[elem.name for elem in main_content.children if elem.name]}")
            else:
                logger.warning("Main content div not found")
                logger.info(f"Available top-level divs: {[div.get('class', []) for div in soup.find_all('div', recursive=False)]}")
            
            # 買取価格データを抽出
            kaitori_prices = {}
            
            # 価格情報を含む要素を探す
            price_elements = soup.find_all('div', class_='tr')
            if price_elements:
                logger.info(f"Found {len(price_elements)} price elements")
                for elem in price_elements:
                    try:
                        # 容量を探す
                        capacity_elem = elem.find('h2') or elem.find('div', class_='ttl')
                        # 価格を探す
                        price_elem = elem.find('div', class_='td2wrap') or elem.find('div', class_='td td2')
                        
                        if capacity_elem and price_elem:
                            capacity_text = capacity_elem.text.strip()
                            capacity_match = re.search(r'(\d+)\s*(GB|TB)', capacity_text, re.IGNORECASE)
                            if capacity_match:
                                capacity_num = capacity_match.group(1)
                                capacity_unit = capacity_match.group(2).upper()
                                capacity = f"{capacity_num}{capacity_unit}"
                                price = re.sub(r'[^\d]', '', price_elem.text.strip())
                                if price:
                                    kaitori_prices[capacity] = price
                                    logger.info(f"Found price for {capacity}: {price}")
                                else:
                                    logger.warning(f"Empty price found for {capacity}")
                            else:
                                logger.warning(f"Could not extract capacity from: {capacity_text}")
                        else:
                            logger.warning(f"Missing capacity or price element in: {elem}")
                    except Exception as e:
                        logger.error(f"Error processing price element: {e}")
                        logger.error(f"Element content: {elem}")
                        continue
                
                if not kaitori_prices:
                    logger.warning("No valid price data found in elements")
            else:
                logger.warning("No price elements found")
                logger.info(f"Page title: {soup.title.string if soup.title else 'No title'}")
            
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
        logger.error(f"Stack trace: {traceback.format_exc()}")
        return {
            series: {
                'kaitori': {},
                'official': get_official_prices(series)
            }
        }
