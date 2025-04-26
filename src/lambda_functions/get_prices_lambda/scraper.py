import logging
import os
import re
from datetime import datetime, timezone
from typing import Optional

import requests
import yaml
from bs4 import BeautifulSoup
from pydantic import BaseModel, field_validator
from tenacity import (retry, retry_if_exception_type, stop_after_attempt,
                      wait_exponential)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class ScraperError(Exception):
    """スクレイピングエラーの基底クラス"""
    pass

class HTTPError(ScraperError):
    """HTTPリクエストエラー"""
    pass

class ParseError(ScraperError):
    """データパースエラー"""
    pass

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True
)
def safe_request(url, headers, timeout):
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP request failed: {str(e)}")
        raise HTTPError(f"Failed to fetch {url}: {str(e)}")

def load_config():
    """
    設定ファイルを読み込む
    """
    config_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'config', 'config.production.yaml')
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
        raise

class PriceData(BaseModel):
    model: str
    price: float
    currency: str = "JPY"
    source: str
    timestamp: datetime
    condition: Optional[str] = None
    
    @field_validator('price')
    @classmethod
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError("Price must be positive")
        return round(v, 2)
    
    @field_validator('model')
    @classmethod
    def validate_model(cls, v):
        if not re.match(r'^iPhone \d{1,2}(?: Pro| Pro Max)? \d{1,3}GB$', v):
            raise ValueError("Invalid model format")
        return v

def normalize_price_data(raw_data):
    try:
        return PriceData(
            model=raw_data['model'],
            price=float(raw_data['price'].replace(',', '')),
            source=raw_data['source'],
            timestamp=datetime.now(timezone.utc),
            condition=raw_data.get('condition')
        )
    except Exception as e:
        logger.error(f"Failed to normalize price data: {str(e)}")
        raise ParseError(f"Data normalization failed: {str(e)}")

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((HTTPError, ParseError)),
    before_sleep=lambda retry_state: logger.warning(
        f"Retrying {retry_state.fn.__name__} after {retry_state.attempt_number} attempts"
    )
)
def get_kaitori_prices():
    config = load_config()
    prices = []
    
    for url in config['scraper']['kaitori_rudea_urls']:
        try:
            response = safe_request(
                url,
                headers={'User-Agent': config['scraper']['user_agent']},
                timeout=config['scraper']['request_timeout']
            )
            soup = BeautifulSoup(response.text, 'html.parser')
            # TODO: スクレイピングロジックの実装
            price_data = normalize_price_data({
                'model': 'iPhone 15 128GB',  # テスト用
                'price': '120000',
                'source': url
            })
            prices.append(price_data)
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            raise ScraperError(f"Failed to scrape {url}: {str(e)}")
    
    return prices

def get_official_prices():
    config = load_config()
    prices = []
    
    try:
        response = safe_request(
            config['scraper']['apple_store_url'],
            headers={'User-Agent': config['scraper']['user_agent']},
            timeout=config['scraper']['request_timeout']
        )
        soup = BeautifulSoup(response.text, 'html.parser')
        # TODO: スクレイピングロジックの実装
        price_data = normalize_price_data({
            'model': 'iPhone 15 128GB',  # テスト用
            'price': '120000',
            'source': config['scraper']['apple_store_url']
        })
        prices.append(price_data)
    except Exception as e:
        logger.error(f"Error scraping Apple Store: {str(e)}")
        raise ScraperError(f"Failed to scrape Apple Store: {str(e)}")
    
    return prices