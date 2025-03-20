import json
import logging
import os
import re
from pathlib import Path

import boto3
import requests
import yaml
from bs4 import BeautifulSoup

logger = logging.getLogger()
logger.setLevel(logging.INFO)

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
        
        response = table.get_item(
            Key={'series': series}
        )
        
        if 'Item' in response:
            logger.info(f"Found official prices for {series}: {response['Item']}")
            # pricesマップから価格データを取得
            return response['Item'].get('prices', {})
        else:
            logger.warning(f"No official prices found for {series}")
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
            'iPhone 16e': config['scraper']['kaitori_rudea_urls'][3]
        }
        
        if series not in series_url_map:
            logger.warning(f"No URL configured for series: {series}")
            return {}

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
            
            logger.info(f"Returning data for {series}: {json.dumps(result, indent=4)}")
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
