import concurrent.futures
import json
import logging
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from statistics import mean, median, stdev
from typing import Any, Dict, List, Optional, Union

import requests
import yaml
from bs4 import BeautifulSoup
from pydantic import BaseModel, field_validator
from tenacity import (after_log, before_sleep_log, retry,
                      retry_if_exception_type, stop_after_attempt,
                      wait_exponential)


# ロギング設定
class ScraperFormatter(logging.Formatter):
    """カスタムログフォーマッタ"""
    def format(self, record):
        # 基本情報
        log_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'function': record.funcName,
            'line': record.lineno
        }
        
        # 追加情報
        if hasattr(record, 'extra'):
            log_data.update(record.extra)
        
        return str(log_data)

def setup_logger():
    """ロガーのセットアップ"""
    logger = logging.getLogger('price_scraper')
    logger.setLevel(logging.INFO)
    
    # 既存のハンドラをクリア
    logger.handlers = []
    
    # コンソールハンドラ
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(ScraperFormatter())
    logger.addHandler(console_handler)
    
    # ファイルハンドラ
    log_file = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'logs', 'scraper.log')
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(ScraperFormatter())
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logger()

def log_with_context(message: str, level: int = logging.INFO, **kwargs):
    """コンテキスト情報を含むログ出力"""
    extra = {
        'context': {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            **kwargs
        }
    }
    logger.log(level, message, extra=extra)

def log_scraping_start(url: str):
    """スクレイピング開始のログ"""
    log_with_context(
        "Starting scraping",
        url=url,
        timestamp=datetime.now(timezone.utc).isoformat()
    )

def log_scraping_success(url: str, items_found: int):
    """スクレイピング成功のログ"""
    log_with_context(
        "Scraping completed successfully",
        url=url,
        items_found=items_found,
        timestamp=datetime.now(timezone.utc).isoformat()
    )

def log_scraping_error(url: str, error: Exception):
    """スクレイピングエラーのログ"""
    log_with_context(
        "Scraping failed",
        url=url,
        error_type=type(error).__name__,
        error_message=str(error),
        timestamp=datetime.now(timezone.utc).isoformat(),
        level=logging.ERROR
    )

def log_price_data(price_data: Dict[str, Any]):
    """価格データのログ"""
    log_with_context(
        "Price data found",
        model=price_data['model'],
        price=price_data['price'],
        source=price_data['source'],
        condition=price_data.get('condition'),
        timestamp=datetime.now(timezone.utc).isoformat()
    )

def log_validation_error(field: str, value: Any, error: str):
    """検証エラーのログ"""
    log_with_context(
        "Validation error",
        field=field,
        value=value,
        error=error,
        timestamp=datetime.now(timezone.utc).isoformat(),
        level=logging.WARNING
    )

class ErrorSeverity(Enum):
    """エラーの重大度を定義する列挙型"""
    LOW = "LOW"      # 軽微なエラー、処理は継続可能
    MEDIUM = "MEDIUM"  # 中程度のエラー、一部の機能に影響
    HIGH = "HIGH"    # 重大なエラー、処理の中断が必要

class ScraperError(Exception):
    """スクレイピングエラーの基底クラス"""
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.severity = severity
        self.context = context or {}
        self.timestamp = datetime.now(timezone.utc)
        self.error_id = f"ERR-{int(time.time())}-{hash(message) % 10000:04d}"
        
        # エラーログを記録
        log_error(self)

class HTTPError(ScraperError):
    """HTTPリクエストエラー"""
    def __init__(self, message: str, status_code: Optional[int] = None, url: Optional[str] = None):
        context = {}
        if status_code:
            context['status_code'] = status_code
        if url:
            context['url'] = url
        super().__init__(message, ErrorSeverity.HIGH, context)

class ParseError(ScraperError):
    """データパースエラー"""
    def __init__(self, message: str, html: Optional[str] = None, selector: Optional[str] = None):
        context = {}
        if html:
            context['html_snippet'] = html[:200]  # 最初の200文字のみを記録
        if selector:
            context['selector'] = selector
        super().__init__(message, ErrorSeverity.MEDIUM, context)

class ValidationError(ScraperError):
    """データ検証エラー"""
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None):
        context = {}
        if field:
            context['field'] = field
        if value:
            context['value'] = str(value)
        super().__init__(message, ErrorSeverity.LOW, context)

class CacheError(ScraperError):
    """キャッシュ関連のエラー"""
    def __init__(self, message: str, operation: str, cache_path: Optional[Path] = None):
        context = {'operation': operation}
        if cache_path:
            context['cache_path'] = str(cache_path)
        super().__init__(message, ErrorSeverity.LOW, context)

class ConfigError(ScraperError):
    """設定ファイルエラー"""
    pass

# リトライ設定
RETRY_CONFIG = {
    'max_attempts': 3,
    'wait_min': 4,
    'wait_max': 10,
    'wait_multiplier': 1
}

def create_retry_decorator():
    """リトライデコレータの作成"""
    return retry(
        stop=stop_after_attempt(RETRY_CONFIG['max_attempts']),
        wait=wait_exponential(
            multiplier=RETRY_CONFIG['wait_multiplier'],
            min=RETRY_CONFIG['wait_min'],
            max=RETRY_CONFIG['wait_max']
        ),
        retry=retry_if_exception_type((HTTPError, ParseError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.INFO),
        reraise=True
    )

def log_error(error: ScraperError) -> None:
    """エラーをログに記録"""
    log_data = {
        'error_id': error.error_id,
        'severity': error.severity.name,
        'message': str(error),
        'timestamp': error.timestamp.isoformat(),
        'context': error.context
    }
    logger.error(json.dumps(log_data, ensure_ascii=False))

def safe_request(url: str, headers: Dict[str, str], timeout: int) -> requests.Response:
    """安全なHTTPリクエストを実行"""
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response
    except requests.exceptions.Timeout:
        raise HTTPError(f"Request timeout after {timeout} seconds", url=url)
    except requests.exceptions.ConnectionError:
        raise HTTPError("Failed to establish connection", url=url)
    except requests.exceptions.HTTPError as e:
        raise HTTPError(
            f"HTTP error {e.response.status_code}: {e.response.reason}",
            status_code=e.response.status_code,
            url=url
        )
    except requests.exceptions.RequestException as e:
        raise HTTPError(f"Request failed: {str(e)}", url=url)

def load_config():
    """
    設定ファイルを読み込む
    """
    config_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'config', 'config.production.yaml')
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            if not config or 'scraper' not in config:
                raise ConfigError("Invalid configuration: missing 'scraper' section")
            return config
    except FileNotFoundError:
        logger.error(f"Config file not found: {config_path}")
        raise ConfigError(f"Configuration file not found: {config_path}")
    except yaml.YAMLError as e:
        logger.error(f"Error parsing config file: {str(e)}")
        raise ConfigError(f"Invalid YAML format: {str(e)}")
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
        raise ConfigError(f"Failed to load configuration: {str(e)}")

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
        if v > 1000000:  # 100万円以上の価格は異常値として扱う
            raise ValueError("Price seems too high")
        return round(v, 2)
    
    @field_validator('model')
    @classmethod
    def validate_model(cls, v):
        # iPhoneモデルの正規表現パターン
        model_pattern = r'^iPhone (?:SE|1[0-5])(?: Pro| Pro Max)? \d{1,3}(?:GB|TB)$'
        if not re.match(model_pattern, v):
            raise ValueError(f"Invalid model format: {v}. Expected format: iPhone [model] [capacity]")
        return v
    
    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v):
        if v not in ["JPY", "USD", "EUR"]:
            raise ValueError("Currency must be JPY, USD, or EUR")
        return v
    
    @field_validator('condition')
    @classmethod
    def validate_condition(cls, v):
        if v and v not in ["新品", "中古", "未使用"]:
            raise ValueError("Condition must be 新品, 中古, or 未使用")
        return v
    
    @field_validator('source')
    @classmethod
    def validate_source(cls, v):
        if not v.startswith(("http://", "https://")):
            raise ValueError("Source must be a valid URL")
        return v
    
    @field_validator('timestamp')
    @classmethod
    def validate_timestamp(cls, v):
        if v.tzinfo is None:
            raise ValueError("Timestamp must be timezone-aware")
        return v

def normalize_price_data(raw_data):
    try:
        # 価格の正規化
        price = raw_data['price']
        if isinstance(price, str):
            price = price.replace(',', '').replace('¥', '').replace('￥', '')
        
        # モデル名の正規化
        model = raw_data['model']
        model = re.sub(r'\s+', ' ', model).strip()  # 余分な空白を削除
        
        # 条件の正規化
        condition = raw_data.get('condition', '新品')
        condition_map = {
            'new': '新品',
            'used': '中古',
            'unused': '未使用'
        }
        condition = condition_map.get(condition.lower(), condition)
        
        return PriceData(
            model=model,
            price=float(price),
            source=raw_data['source'],
            timestamp=datetime.now(timezone.utc),
            condition=condition
        )
    except KeyError as e:
        logger.error(f"Missing required field: {str(e)}")
        raise ValidationError(f"Missing required field: {str(e)}")
    except ValueError as e:
        logger.error(f"Invalid data format: {str(e)}")
        raise ValidationError(f"Invalid data format: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to normalize price data: {str(e)}")
        raise ValidationError(f"Data normalization failed: {str(e)}")

# 並列処理の設定
MAX_WORKERS = 5  # 同時に実行する最大スレッド数
TIMEOUT = 30     # 各タスクのタイムアウト（秒）

@dataclass
class PerformanceMetrics:
    """パフォーマンスメトリクスのデータクラス"""
    url: str
    start_time: float
    end_time: float
    response_time: float
    success: bool
    error_message: Optional[str] = None
    items_found: int = 0

class PerformanceTracker:
    """パフォーマンス計測と分析を行うクラス"""
    def __init__(self):
        self.metrics: List[PerformanceMetrics] = []
        self._start_time = time.time()
    
    def start_scraping(self, url: str) -> float:
        """スクレイピング開始時のタイムスタンプを記録"""
        return time.time()
    
    def end_scraping(self, url: str, start_time: float, success: bool, 
                    error_message: Optional[str] = None, items_found: int = 0) -> None:
        """スクレイピング終了時のメトリクスを記録"""
        end_time = time.time()
        self.metrics.append(PerformanceMetrics(
            url=url,
            start_time=start_time,
            end_time=end_time,
            response_time=end_time - start_time,
            success=success,
            error_message=error_message,
            items_found=items_found
        ))
    
    def get_summary(self) -> Dict[str, float]:
        """パフォーマンスメトリクスのサマリーを返す"""
        if not self.metrics:
            return {}
        
        response_times = [m.response_time for m in self.metrics]
        success_count = sum(1 for m in self.metrics if m.success)
        total_items = sum(m.items_found for m in self.metrics)
        
        return {
            'total_requests': len(self.metrics),
            'success_rate': success_count / len(self.metrics) * 100,
            'total_items_found': total_items,
            'avg_response_time': mean(response_times),
            'median_response_time': median(response_times),
            'std_dev_response_time': stdev(response_times) if len(response_times) > 1 else 0,
            'min_response_time': min(response_times),
            'max_response_time': max(response_times),
            'total_execution_time': time.time() - self._start_time
        }
    
    def log_summary(self) -> None:
        """パフォーマンスサマリーをログに出力"""
        summary = self.get_summary()
        if not summary:
            logger.warning("No performance metrics available")
            return
        
        logger.info("Performance Summary:")
        logger.info(f"Total Requests: {summary['total_requests']}")
        logger.info(f"Success Rate: {summary['success_rate']:.2f}%")
        logger.info(f"Total Items Found: {summary['total_items_found']}")
        logger.info(f"Average Response Time: {summary['avg_response_time']:.2f}s")
        logger.info(f"Median Response Time: {summary['median_response_time']:.2f}s")
        logger.info(f"Standard Deviation: {summary['std_dev_response_time']:.2f}s")
        logger.info(f"Min Response Time: {summary['min_response_time']:.2f}s")
        logger.info(f"Max Response Time: {summary['max_response_time']:.2f}s")
        logger.info(f"Total Execution Time: {summary['total_execution_time']:.2f}s")

# グローバルなパフォーマンストラッカー
performance_tracker = PerformanceTracker()

class CacheManager:
    """キャッシュ管理クラス"""
    def __init__(self, cache_dir: str = "cache", cache_duration: int = 3600):
        self.cache_dir = Path(cache_dir)
        self.cache_duration = cache_duration  # キャッシュの有効期間（秒）
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_path(self, url: str) -> Path:
        """URLに対応するキャッシュファイルのパスを生成"""
        cache_key = url.replace('/', '_').replace(':', '_')
        return self.cache_dir / f"{cache_key}.json"
    
    def _is_cache_valid(self, cache_path: Path) -> bool:
        """キャッシュが有効かどうかを確認"""
        if not cache_path.exists():
            return False
        
        cache_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
        return datetime.now() - cache_time < timedelta(seconds=self.cache_duration)
    
    def get_cached_data(self, url: str) -> Optional[List[Dict[str, Any]]]:
        """キャッシュからデータを取得"""
        cache_path = self._get_cache_path(url)
        
        if not self._is_cache_valid(cache_path):
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"Cache hit for {url}")
                return data
        except Exception as e:
            logger.warning(f"Failed to read cache for {url}: {str(e)}")
            return None
    
    def save_to_cache(self, url: str, data: List[Dict[str, Any]]) -> None:
        """データをキャッシュに保存"""
        cache_path = self._get_cache_path(url)
        
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Cache saved for {url}")
        except Exception as e:
            logger.warning(f"Failed to save cache for {url}: {str(e)}")
    
    def clear_cache(self) -> None:
        """キャッシュをクリア"""
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            logger.info("Cache cleared")
        except Exception as e:
            logger.warning(f"Failed to clear cache: {str(e)}")

# グローバルなキャッシュマネージャー
cache_manager = CacheManager()

class ErrorHandler:
    """エラーハンドリングを管理するクラス"""
    def __init__(self):
        self.errors: List[ScraperError] = []
        self.error_counts = {
            ErrorSeverity.LOW: 0,
            ErrorSeverity.MEDIUM: 0,
            ErrorSeverity.HIGH: 0
        }
    
    def handle_error(self, error: ScraperError) -> None:
        """エラーを処理し、記録する"""
        self.errors.append(error)
        self.error_counts[error.severity] += 1
        
        # エラーの重大度に応じた処理
        if error.severity == ErrorSeverity.HIGH:
            logger.error(f"Critical error occurred: {error}")
        elif error.severity == ErrorSeverity.MEDIUM:
            logger.warning(f"Warning: {error}")
        else:
            logger.info(f"Minor error: {error}")
    
    def get_error_summary(self) -> Dict[str, Any]:
        """エラーのサマリーを返す"""
        return {
            'total_errors': len(self.errors),
            'error_counts': {
                severity.name: count
                for severity, count in self.error_counts.items()
            },
            'recent_errors': [
                {
                    'error_id': error.error_id,
                    'message': str(error),
                    'severity': error.severity.name,
                    'timestamp': error.timestamp.isoformat(),
                    'context': error.context
                }
                for error in self.errors[-5:]  # 最近の5件のエラー
            ]
        }
    
    def should_continue(self) -> bool:
        """処理を継続すべきかどうかを判断"""
        # HIGHレベルのエラーが3件以上発生した場合は処理を中断
        return self.error_counts[ErrorSeverity.HIGH] < 3

# グローバルなエラーハンドラー
error_handler = ErrorHandler()

def validate_price_data(data: Dict[str, Any]) -> None:
    """価格データの検証"""
    try:
        if not data.get('model'):
            raise ValidationError("Model name is required", field='model')
        
        if not data.get('price'):
            raise ValidationError("Price is required", field='price')
        
        price = float(data['price'])
        if price <= 0:
            raise ValidationError("Price must be positive", field='price', value=price)
        if price > 1000000:  # 100万円以上の価格は異常値として扱う
            raise ValidationError("Price seems too high", field='price', value=price)
        
        if not data.get('source'):
            raise ValidationError("Source URL is required", field='source')
        
    except ValueError as e:
        raise ValidationError(f"Invalid price format: {str(e)}", field='price', value=data.get('price'))

def scrape_url(url: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """単一URLのスクレイピングを実行"""
    try:
        # キャッシュからデータを取得
        cached_data = cache_manager.get_cached_data(url)
        if cached_data is not None:
            return cached_data
        
        start_time = performance_tracker.start_scraping(url)
        log_scraping_start(url)
        prices = []
        
        try:
            response = safe_request(
                url,
                headers={'User-Agent': config['scraper']['user_agent']},
                timeout=config['scraper']['request_timeout']
            )
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 価格情報を含む要素を探す
            price_elements = soup.find_all('div', class_='tr')
            if not price_elements:
                raise ParseError("No price elements found", url=url)
            
            for elem in price_elements:
                try:
                    # 容量を探す
                    capacity_elem = elem.find('h2') or elem.find('div', class_='ttl')
                    # 価格を探す
                    price_elem = elem.find('div', class_='td2wrap') or elem.find('div', class_='td td2')
                    
                    if not (capacity_elem and price_elem):
                        raise ParseError("Missing capacity or price element", selector='div.tr')
                    
                    capacity_text = capacity_elem.text.strip()
                    capacity_match = re.search(r'(\d+)\s*(GB|TB)', capacity_text, re.IGNORECASE)
                    if not capacity_match:
                        raise ParseError("Could not extract capacity", html=capacity_text)
                    
                    capacity_num = capacity_match.group(1)
                    capacity_unit = capacity_match.group(2).upper()
                    capacity = f"{capacity_num}{capacity_unit}"
                    
                    # モデル名を抽出
                    model_match = re.search(r'iPhone \d{1,2}(?: Pro| Pro Max)?', capacity_text)
                    if not model_match:
                        raise ParseError("Could not extract model", html=capacity_text)
                    
                    model = f"{model_match.group()} {capacity}"
                    price = re.sub(r'[^\d]', '', price_elem.text.strip())
                    
                    if not price:
                        raise ValidationError("Empty price found", field='price', value=price_elem.text)
                    
                    price_data = {
                        'model': model,
                        'price': price,
                        'source': url,
                        'condition': '新品' if '新品' in capacity_text else '中古'
                    }
                    
                    # データの検証
                    validate_price_data(price_data)
                    
                    prices.append(price_data)
                    log_price_data(price_data)
                    
                except (ParseError, ValidationError) as e:
                    error_handler.handle_error(e)
                    continue
            
            log_scraping_success(url, len(prices))
            performance_tracker.end_scraping(url, start_time, True, items_found=len(prices))
            
            # キャッシュに保存
            if prices:
                try:
                    cache_manager.save_to_cache(url, prices)
                except Exception as e:
                    error_handler.handle_error(CacheError(
                        f"Failed to save cache: {str(e)}",
                        operation="save",
                        cache_path=cache_manager._get_cache_path(url)
                    ))
            
            return prices
            
        except Exception as e:
            log_scraping_error(url, e)
            performance_tracker.end_scraping(url, start_time, False, str(e))
            raise
    
    except Exception as e:
        if not isinstance(e, ScraperError):
            e = ScraperError(str(e))
        error_handler.handle_error(e)
        if not error_handler.should_continue():
            raise ScraperError("Too many critical errors occurred", ErrorSeverity.HIGH)
        return []

@create_retry_decorator()
def get_kaitori_prices():
    """並列処理を使用して複数URLから価格情報を取得"""
    config = load_config()
    all_prices = []
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # 各URLのスクレイピングタスクをスケジュール
        future_to_url = {
            executor.submit(scrape_url, url, config): url
            for url in config['scraper']['kaitori_rudea_urls']
        }
        
        # 完了したタスクを処理
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                prices = future.result(timeout=TIMEOUT)
                all_prices.extend(prices)
            except Exception as e:
                log_scraping_error(url, e)
                continue
    
    # パフォーマンスサマリーをログに出力
    performance_tracker.log_summary()
    return all_prices

@create_retry_decorator()
def get_official_prices():
    """公式価格の取得（単一URLのため並列処理なし）"""
    config = load_config()
    prices = []
    
    try:
        response = safe_request(
            config['scraper']['apple_store_url'],
            headers={'User-Agent': config['scraper']['user_agent']},
            timeout=config['scraper']['request_timeout']
        )
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 価格情報を含む要素を探す
        price_elements = soup.find_all('div', class_='as-producttile')
        if not price_elements:
            logger.warning("No price elements found in Apple Store")
            return prices
        
        for elem in price_elements:
            try:
                # モデル名を探す
                model_elem = elem.find('span', class_='as-producttile-title')
                # 価格を探す
                price_elem = elem.find('span', class_='as-price-currentprice')
                
                if model_elem and price_elem:
                    model_text = model_elem.text.strip()
                    price_text = price_elem.text.strip()
                    
                    # モデル名から容量を抽出
                    capacity_match = re.search(r'(\d+)\s*(GB|TB)', model_text, re.IGNORECASE)
                    if capacity_match:
                        capacity_num = capacity_match.group(1)
                        capacity_unit = capacity_match.group(2).upper()
                        capacity = f"{capacity_num}{capacity_unit}"
                        
                        # モデル名を抽出
                        model_match = re.search(r'iPhone \d{1,2}(?: Pro| Pro Max)?', model_text)
                        if model_match:
                            model = f"{model_match.group()} {capacity}"
                            price = re.sub(r'[^\d]', '', price_text)
                            
                            if price:
                                price_data = {
                                    'model': model,
                                    'price': price,
                                    'source': config['scraper']['apple_store_url'],
                                    'condition': '新品'
                                }
                                prices.append(price_data)
                                log_price_data(price_data)
                            else:
                                logger.warning(f"Empty price found for {model}")
                        else:
                            logger.warning(f"Could not extract model from: {model_text}")
                    else:
                        logger.warning(f"Could not extract capacity from: {model_text}")
                else:
                    logger.warning(f"Missing model or price element in: {elem}")
            except Exception as e:
                logger.error(f"Error processing price element: {e}")
                logger.error(f"Element content: {elem}")
                continue
            
    except Exception as e:
        logger.error(f"Error scraping Apple Store: {str(e)}")
        raise ScraperError(f"Failed to scrape Apple Store: {str(e)}")
    
    return prices