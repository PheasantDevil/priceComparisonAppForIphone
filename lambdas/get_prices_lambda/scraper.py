import json
import logging
import os
import re
import time
from datetime import datetime, timezone
from typing import Optional

import boto3
import requests
import yaml
from bs4 import BeautifulSoup
from pydantic import BaseModel, validator
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

class RetryTracker:
    def __init__(self):
        self.attempts = {}
    
    def track_attempt(self, url):
        if url not in self.attempts:
            self.attempts[url] = 0
        self.attempts[url] += 1
        return self.attempts[url]

retry_tracker = RetryTracker()

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

def notify_error(error_message):
    sns = boto3.client('sns')
    try:
        sns.publish(
            TopicArn=os.environ['ERROR_NOTIFICATION_TOPIC_ARN'],
            Message=json.dumps({
                'error': error_message,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        )
    except Exception as e:
        logger.error(f"Failed to send error notification: {str(e)}")

def load_config():
    """
    設定ファイルを読み込む
    """
    config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'config.production.yaml')
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
        raise

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
    prices = {}
    
    for url in config['scraper']['kaitori_rudea_urls']:
        attempt = retry_tracker.track_attempt(url)
        try:
            response = safe_request(
                url,
                headers={'User-Agent': config['scraper']['user_agent']},
                timeout=config['scraper']['request_timeout']
            )
            # スクレイピングロジック
        except Exception as e:
            if attempt >= 3:
                notify_error(f"Failed to scrape {url} after {attempt} attempts: {str(e)}")
            raise
    
    return prices

def get_official_prices():
    """
    Apple Storeの公式価格を取得
    """
    config = load_config()
    prices = {}
    
    try:
        response = requests.get(
            config['scraper']['apple_store_url'],
            headers={'User-Agent': config['scraper']['user_agent']},
            timeout=config['scraper']['request_timeout']
        )
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        # TODO: スクレイピングロジックの実装
        
    except Exception as e:
        logger.error(f"Error scraping Apple Store: {str(e)}")
    
    return prices 

class PriceData(BaseModel):
    model: str
    price: float
    currency: str = "JPY"
    source: str
    timestamp: datetime
    condition: Optional[str] = None
    
    @validator('price')
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError("Price must be positive")
        return round(v, 2)
    
    @validator('model')
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