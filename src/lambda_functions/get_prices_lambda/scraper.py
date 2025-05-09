import concurrent.futures
import hashlib
import json
import logging
import os
import random
import re
import time
import uuid
import warnings
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from statistics import mean, median, stdev
from typing import Any, ContextManager, Dict, List, Optional, Union

import requests
import yaml
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field, HttpUrl, field_validator, validator
from tenacity import (after_log, before_sleep_log, retry,
                      retry_if_exception_type, stop_after_attempt,
                      wait_exponential)

# 定数定義
MAX_WORKERS = 5  # 同時に実行する最大スレッド数
TIMEOUT = 60     # 各タスクのタイムアウト（秒）を60秒に延長
CACHE_DURATION = 3600  # キャッシュの有効期間（秒）

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
    log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'logs'))
    os.makedirs(log_dir, mode=0o755, exist_ok=True)
    log_file = os.path.join(log_dir, 'scraper.log')
    file_handler = logging.FileHandler(log_file, mode='a')
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

class ErrorType(Enum):
    HTTP = "HTTP"
    PARSE = "PARSE"
    VALIDATION = "VALIDATION"
    CACHE = "CACHE"
    SCRAPER = "SCRAPER"

class ErrorSeverity(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class ScraperError(Exception):
    def __init__(self, message: str, error_type: Union[ErrorType, str] = ErrorType.SCRAPER, severity: ErrorSeverity = ErrorSeverity.HIGH, context: Optional[Dict] = None):
        super().__init__(message)
        self.message = message
        self.error_type = error_type if isinstance(error_type, ErrorType) else ErrorType.SCRAPER
        self.severity = severity if isinstance(severity, ErrorSeverity) else ErrorSeverity.HIGH
        self.context = context or {}
        self.error_id = f"ERR-{int(time.time())}-{random.randint(1000, 9999)}"
        self.timestamp = datetime.now(timezone.utc)

class HTTPError(ScraperError):
    def __init__(self, message: str, status_code: Optional[int] = None, url: Optional[str] = None):
        context = {
            'status_code': status_code,
            'url': url
        } if status_code and url else {}
        super().__init__(message, ErrorType.HTTP, ErrorSeverity.HIGH, context)

class ParseError(ScraperError):
    def __init__(self, message: str, html: str = '', selector: str = ''):
        html_snippet = html[:200] if len(html) > 200 else html
        context = {
            'html_snippet': html_snippet,
            'selector': selector
        }
        super().__init__(message, ErrorType.PARSE, ErrorSeverity.MEDIUM, context)

class ValidationError(ScraperError):
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[str] = None):
        context = {
            'field': field,
            'value': str(value)
        } if field else {}
        super().__init__(message, ErrorType.VALIDATION, ErrorSeverity.LOW, context)

class CacheError(ScraperError):
    def __init__(self, message: str, operation: str = '', cache_path: Union[str, Path] = ''):
        context = {
            'operation': operation,
            'cache_path': str(cache_path)
        }
        super().__init__(message, ErrorType.CACHE, ErrorSeverity.LOW, context)

class ConfigError(ScraperError):
    """設定ファイルエラー"""
    pass

# リトライ設定
RETRY_CONFIG = {
    'max_attempts': 5,  # リトライ回数を5回に増加
    'wait_min': 2,      # 最小待機時間を2秒に短縮
    'wait_max': 30,     # 最大待機時間を30秒に延長
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

def safe_request(url: str, headers: Dict[str, str], timeout: int = TIMEOUT) -> requests.Response:
    """安全なHTTPリクエストを実行"""
    try:
        response = requests.get(url, headers=headers, timeout=timeout, verify=True)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        raise HTTPError(f"Request failed: {str(e)}", url=url)

def load_config():
    """
    設定ファイルを読み込む
    """
    try:
        # 環境変数から設定ファイルのパスを取得
        config_path = os.getenv('CONFIG_FILE', os.path.join(os.path.dirname(__file__), '..', '..', '..', 'config', 'config.production.yaml'))
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            if not config:
                raise ConfigError("Configuration file is empty")
            
            # 必須の設定項目を確認
            required_sections = ['scraper']
            for section in required_sections:
                if section not in config:
                    raise ConfigError(f"Missing required section: {section}")
            
            # scraperセクションの必須項目を確認
            required_scraper_settings = ['kaitori_rudea_urls', 'request_timeout', 'retry_count']
            for setting in required_scraper_settings:
                if setting not in config['scraper']:
                    raise ConfigError(f"Missing required scraper setting: {setting}")
            
            logger.info(f"Successfully loaded configuration from {config_path}")
            return config
    except FileNotFoundError:
        error_msg = f"Config file not found: {config_path}"
        logger.error(error_msg)
        raise ConfigError(error_msg)
    except yaml.YAMLError as e:
        error_msg = f"Error parsing config file: {str(e)}"
        logger.error(error_msg)
        raise ConfigError(error_msg)
    except Exception as e:
        error_msg = f"Error loading config: {str(e)}"
        logger.error(error_msg)
        raise ConfigError(error_msg)

class PriceData(BaseModel):
    """価格データモデル"""
    model: str
    price: float
    source: str  # Changed from HttpUrl to str to handle source type strings
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    url: Optional[str] = None
    condition: Optional[str] = None
    notes: Optional[str] = None
    currency: str = "JPY"

    def to_dict(self) -> Dict[str, Any]:
        data = self.model_dump()
        if isinstance(data['timestamp'], datetime):
            data['timestamp'] = data['timestamp'].isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PriceData':
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

    @validator('price')
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError('Price must be positive')
        return v

    @field_validator('model')
    @classmethod
    def validate_model(cls, v: str) -> str:
        """モデル名の検証"""
        if not v or not isinstance(v, str):
            raise ValueError("Model must be a non-empty string")
        # iPhoneモデルの正規表現パターン
        pattern = r'^iPhone\s+\d+(\s+Pro(\s+Max)?)?(\s+\d+GB)?$'
        if not re.match(pattern, v):
            raise ValueError("Invalid iPhone model format")
        return v

    @field_validator('condition')
    @classmethod
    def validate_condition(cls, v: Optional[str]) -> Optional[str]:
        """状態の検証"""
        if v is None:
            return v
        valid_conditions = ['新品', '中古', 'リファービッシュ']
        if v not in valid_conditions:
            raise ValueError(f"Invalid condition. Must be one of: {', '.join(valid_conditions)}")
        return v

    @field_validator('source')
    @classmethod
    def validate_source(cls, v: str) -> str:
        """ソースの検証"""
        if not v or not isinstance(v, str):
            raise ValueError("Source must be a non-empty string")
        valid_sources = ['kaitori', 'official']
        if v not in valid_sources:
            raise ValueError(f"Source must be one of: {', '.join(valid_sources)}")
        return v

    @field_validator('timestamp')
    @classmethod
    def validate_timestamp(cls, v: datetime) -> datetime:
        """タイムスタンプの検証"""
        if not isinstance(v, datetime):
            raise ValueError("Timestamp must be a datetime object")
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
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
    """パフォーマンスメトリクスのトラッキング"""
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.request_durations = defaultdict(list)
        self.cache_hits = defaultdict(int)
        self.cache_misses = defaultdict(int)
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0

    def start_scraping(self):
        """スクレイピングの開始時刻を記録"""
        self.start_time = time.time()

    def end_scraping(self):
        """スクレイピングの終了時刻を記録"""
        self.end_time = time.time()

    def record_request(self, url: str, duration: float, success: bool = True):
        """リクエストの実行時間を記録"""
        self.request_durations[url].append(duration)
        self.total_requests += 1
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1

    def record_cache_hit(self, url: str):
        """キャッシュヒットを記録"""
        self.cache_hits[url] += 1

    def record_cache_miss(self, url: str):
        """キャッシュミスを記録"""
        self.cache_misses[url] += 1

    def get_summary(self) -> Dict:
        """パフォーマンスメトリクスのサマリーを取得"""
        if not self.start_time or not self.end_time:
            return {}

        total_duration = self.end_time - self.start_time
        avg_response_time = sum(
            sum(durations) for durations in self.request_durations.values()
        ) / max(self.total_requests, 1)

        total_cache_hits = sum(self.cache_hits.values())
        total_cache_misses = sum(self.cache_misses.values())
        total_cache_requests = total_cache_hits + total_cache_misses
        cache_hit_ratio = (total_cache_hits / total_cache_requests * 100) if total_cache_requests > 0 else 0
        success_rate = (self.successful_requests / max(self.total_requests, 1)) * 100

        return {
            'total_duration': total_duration,
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'success_rate': success_rate,
            'avg_response_time': avg_response_time,
            'cache_hits': dict(self.cache_hits),
            'cache_misses': dict(self.cache_misses),
            'cache_hit_ratio': cache_hit_ratio,
            'request_durations': dict(self.request_durations)
        }

    def clear(self):
        """パフォーマンスメトリクスをクリアする"""
        self.start_time = None
        self.end_time = None
        self.request_durations.clear()
        self.cache_hits.clear()
        self.cache_misses.clear()
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0

class ErrorHandler:
    def __init__(self):
        self.error_counts = {severity: 0 for severity in ErrorSeverity}
        self.error_types = {error_type: 0 for error_type in ErrorType}
        self.recent_errors = []
        self.max_recent_errors = 10
        self.errors = []  # 全てのエラーを保持

    def handle_error(self, error: Union[ScraperError, Exception]):
        """エラーを処理し、ログに記録する"""
        if not isinstance(error, ScraperError):
            error = ScraperError(str(error))

        self.error_counts[error.severity] += 1
        self.error_types[error.error_type] += 1
        
        error_info = {
            'error_id': error.error_id,
            'severity': error.severity.name,
            'message': str(error),
            'timestamp': error.timestamp.isoformat(),
            'context': error.context
        }
        
        self.recent_errors.append(error_info)
        self.errors.append(error)
        if len(self.recent_errors) > self.max_recent_errors:
            self.recent_errors.pop(0)
            
        log_error(error)

    def get_summary(self) -> Dict:
        """エラーサマリーを取得する"""
        return {
            'total_errors': sum(self.error_counts.values()),
            'error_counts': {severity.name: count for severity, count in self.error_counts.items()},
            'error_types': {error_type.name: count for error_type, count in self.error_types.items()},
            'recent_errors': self.recent_errors
        }

    def should_continue(self) -> bool:
        """スクレイピングを続行すべきかを判断する"""
        high_severity_count = self.error_counts[ErrorSeverity.HIGH]
        return high_severity_count < 3

    def clear(self):
        """エラー情報をクリアする"""
        self.error_counts = {severity: 0 for severity in ErrorSeverity}
        self.error_types = {error_type: 0 for error_type in ErrorType}
        self.recent_errors = []
        self.errors = []

class CacheManager:
    """キャッシュを管理するクラス"""
    def __init__(self, cache_dir: str = 'cache', cache_ttl: int = 3600, cache_duration: Optional[int] = None):
        self.cache_dir = Path(cache_dir)
        # Support legacy cache_duration parameter with deprecation warning
        if cache_duration is not None:
            warnings.warn(
                "The 'cache_duration' parameter is deprecated and will be removed in a future version. "
                "Use 'cache_ttl' instead.",
                DeprecationWarning,
                stacklevel=2
            )
            self.cache_ttl = cache_duration
        else:
            self.cache_ttl = cache_ttl
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, url: str) -> Path:
        """URLに基づいてキャッシュファイルのパスを生成する"""
        url_hash = str(hash(url))
        return self.cache_dir / f"{url_hash}.json"

    def _is_cache_valid(self, cache_path: Path) -> bool:
        """キャッシュが有効かどうかを確認する"""
        if not cache_path.exists():
            return False

        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            cache_time = datetime.fromisoformat(cache_data['timestamp'])
            now = datetime.now(timezone.utc)
            
            return (now - cache_time).total_seconds() < self.cache_ttl
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logging.error(f"Cache validation error: {str(e)}")
            return False

    def get_cached_data(self, url: str) -> Optional[List[Dict]]:
        """URLに対応するキャッシュデータを取得する"""
        cache_path = self._get_cache_path(url)
        
        if not self._is_cache_valid(cache_path):
            return None

        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # ISO形式の文字列をdatetimeオブジェクトに変換
            data = cache_data['data']
            for item in data:
                if 'timestamp' in item:
                    item['timestamp'] = datetime.fromisoformat(item['timestamp'])
            
            logging.info(f"Successfully read from cache: {url}")
            return data
        except (json.JSONDecodeError, KeyError, OSError) as e:
            raise CacheError(f"Cache read error: {str(e)}", "read", cache_path)

    def save_to_cache(self, url: str, data: List[Dict]):
        """データをキャッシュに保存する"""
        cache_path = self._get_cache_path(url)
        
        try:
            # datetimeオブジェクトをISO形式の文字列に変換
            serializable_data = []
            for item in data:
                item_copy = item.copy()
                if 'timestamp' in item_copy:
                    item_copy['timestamp'] = item_copy['timestamp'].isoformat()
                serializable_data.append(item_copy)
            
            cache_data = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'data': serializable_data
            }
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            logging.info(f"Successfully cached data for: {url}")
        except (OSError, TypeError) as e:
            logging.error(f"Cache write error: {str(e)}")
            raise CacheError("Cache write failed", "save", cache_path)

    def clear_cache(self):
        """キャッシュディレクトリ内のすべてのファイルを削除する"""
        try:
            for cache_file in self.cache_dir.glob('*.json'):
                cache_file.unlink()
        except OSError as e:
            raise CacheError(f"Cache clear error: {str(e)}", "clear", self.cache_dir)

class Scraper:
    """スクレイピングを実行するクラス"""
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.session = requests.Session()
        self.cache_manager = CacheManager()
        self.error_handler = ErrorHandler()
        self.performance_tracker = PerformanceTracker()

    @contextmanager
    def _measure_request(self, url: str):
        """リクエストの実行時間を計測するコンテキストマネージャ"""
        start_time = time.time()
        success = True
        try:
            yield
        except Exception:
            success = False
            raise
        finally:
            duration = time.time() - start_time
            self.performance_tracker.record_request(url, duration, success)

    def scrape_url(self, url: str, source: str = 'unknown') -> List[Dict]:
        """指定されたURLからデータをスクレイピング"""
        retry_count = 0
        while retry_count < RETRY_CONFIG['max_attempts']:
            try:
                cached_data = self.cache_manager.get_cached_data(url)
                if cached_data:
                    self.performance_tracker.record_cache_hit(url)
                    return cached_data

                self.performance_tracker.record_cache_miss(url)
                
                with self._measure_request(url):
                    response = self.session.get(url, timeout=TIMEOUT)
                    response.raise_for_status()
                    data = self._parse_response(response.text, source)
                    self.cache_manager.save_to_cache(url, data)
                    return data
            except requests.exceptions.RequestException as e:
                retry_count += 1
                if retry_count >= RETRY_CONFIG['max_attempts']:
                    error = HTTPError(f"Request failed after {retry_count} retries: {str(e)}", getattr(e.response, 'status_code', None), url)
                    self.error_handler.handle_error(error)
                    raise error
                wait_time = min(RETRY_CONFIG['wait_max'], RETRY_CONFIG['wait_min'] * (2 ** (retry_count - 1)))
                logger.warning(f"Request failed, retrying in {wait_time} seconds... (Attempt {retry_count}/{RETRY_CONFIG['max_attempts']})")
                time.sleep(wait_time)
            except Exception as e:
                if not isinstance(e, ScraperError):
                    error = ScraperError(f"Scraping failed: {str(e)}", context={
                        'url': url,
                        'source': source,
                        'error_type': str(type(e).__name__)
                    })
                    self.error_handler.handle_error(error)
                    raise error
                self.error_handler.handle_error(e)
                raise e

    def scrape_urls(self, urls: List[str], source: str) -> List[List[Dict[str, Any]]]:
        """
        複数のURLを並列でスクレイピングする
        
        Args:
            urls: スクレイピング対象のURLリスト
            source: データソース（'kaitori'または'official'）
            
        Returns:
            List[List[Dict[str, Any]]]: 各URLの価格データリスト
        """
        results = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_url = {executor.submit(self.scrape_url, url, source): url for url in urls}
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    data = future.result()
                    results.append(data)
                except Exception as e:
                    logger.error(f"Error scraping {url}: {str(e)}")
                    results.append([])
        return results

    def get_kaitori_prices(self) -> List[Dict]:
        """買取価格を取得する"""
        try:
            self.performance_tracker.start_scraping()
            prices = []
            for url in self.config.get('urls', {}).get('kaitori', []):
                try:
                    prices.extend(self.scrape_url(url, 'kaitori'))
                except Exception as e:
                    self.error_handler.handle_error(e)
                    if not self.error_handler.should_continue():
                        break
            return prices
        finally:
            self.performance_tracker.end_scraping()

    def get_official_prices(self) -> List[Dict]:
        """公式価格を取得する"""
        try:
            self.performance_tracker.start_scraping()
            prices = []
            for url in self.config.get('urls', {}).get('official', []):
                try:
                    prices.extend(self.scrape_url(url, 'official'))
                except Exception as e:
                    self.error_handler.handle_error(e)
                    if not self.error_handler.should_continue():
                        break
            return prices
        finally:
            self.performance_tracker.end_scraping()

    def _parse_response(self, html: str, source: str) -> List[Dict]:
        """HTMLレスポンスをパースする"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            if source == 'kaitori':
                items = soup.select('.price-item')
                if not items:
                    raise ParseError("No price items found", html, '.price-item')
                
                prices = []
                for item in items:
                    try:
                        model = item.select_one('.model').text.strip()
                        price = float(item.select_one('.price').text.strip().replace(',', ''))
                        condition = item.select_one('.condition').text.strip()
                        
                        price_data = {
                            'model': model,
                            'price': price,
                            'source': source,
                            'condition': condition,
                            'timestamp': datetime.now(timezone.utc)
                        }
                        
                        if validate_price_data(price_data):
                            prices.append(price_data)
                    except (AttributeError, ValueError) as e:
                        raise ParseError(f"Failed to parse price item: {str(e)}", str(item), source)
                
                return prices
            else:
                items = soup.select('.product-item')
                if not items:
                    raise ParseError("No product items found", html, '.product-item')
                
                prices = []
                for item in items:
                    try:
                        model = item.select_one('.model-name').text.strip()
                        price = float(item.select_one('.price').text.strip().replace(',', ''))
                        
                        price_data = {
                            'model': model,
                            'price': price,
                            'source': source,
                            'timestamp': datetime.now(timezone.utc)
                        }
                        
                        if validate_price_data(price_data):
                            prices.append(price_data)
                    except (AttributeError, ValueError) as e:
                        raise ParseError(f"Failed to parse product item: {str(e)}", str(item), source)
                
                return prices
        except Exception as e:
            if not isinstance(e, ScraperError):
                e = ParseError(f"Failed to parse HTML: {str(e)}", html, source)
            self.error_handler.handle_error(e)
            raise e

    def get_summary(self) -> Dict[str, Any]:
        """スクレイピングの実行結果サマリーを取得"""
        return {
            'performance': self.performance_tracker.get_summary(),
            'errors': self.error_handler.get_summary()
        }

def validate_price_data(data: Dict[str, Any]) -> bool:
    """価格データをバリデーションする"""
    try:
        PriceData(**data)
        return True
    except ValidationError as e:
        logging.error(f"Price data validation error: {str(e)}")
        return False