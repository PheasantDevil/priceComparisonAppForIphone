import concurrent.futures
import hashlib
import json
import logging
import os
import re
import time
import uuid
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
from pydantic import BaseModel, Field, field_validator
from tenacity import (after_log, before_sleep_log, retry,
                      retry_if_exception_type, stop_after_attempt,
                      wait_exponential)

# 定数定義
MAX_WORKERS = 5  # 同時に実行する最大スレッド数
TIMEOUT = 30     # 各タスクのタイムアウト（秒）
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
        super().__init__(message, ErrorSeverity.HIGH)
        self.status_code = status_code
        self.url = url
        self.context = {}
        if status_code:
            self.context['status_code'] = status_code
        if url:
            self.context['url'] = url

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

def safe_request(url: str, headers: Dict[str, str], timeout: int = TIMEOUT) -> requests.Response:
    """安全なHTTPリクエストを実行"""
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response
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
    """価格データモデル"""
    model: str
    price: float
    source: str
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

    @field_validator('price')
    @classmethod
    def validate_price(cls, v: float) -> float:
        """価格の検証"""
        if not isinstance(v, (int, float)):
            raise ValueError("Price must be a number")
        if v <= 0:
            raise ValueError("Price must be positive")
        if v > 1000000:
            raise ValueError("Price is unreasonably high")
        return float(v)

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
        """ソースURLの検証"""
        if not v or not isinstance(v, str):
            raise ValueError("Source must be a non-empty string")
        if not v.startswith(('http://', 'https://')):
            raise ValueError("Source must be a valid URL")
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
    """スクレイピングのパフォーマンスを追跡するクラス"""
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.request_times = []
        self.errors = []

    def start_scraping(self) -> None:
        """スクレイピングの開始時刻を記録"""
        self.start_time = datetime.now()

    def end_scraping(self, success: bool = True) -> None:
        """スクレイピングの終了時刻を記録"""
        self.end_time = datetime.now()
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1

    def record_request(self, url: str, duration: float, success: bool = True) -> None:
        """リクエストの結果を記録"""
        self.total_requests += 1
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
        self.request_times.append({
            'url': url,
            'duration': duration,
            'timestamp': datetime.now(),
            'success': success
        })

    def record_cache_hit(self, url: str) -> None:
        """キャッシュヒットを記録"""
        self.cache_hits += 1
        logger.info(f"Cache hit for URL: {url}")

    def record_cache_miss(self, url: str) -> None:
        """キャッシュミスを記録"""
        self.cache_misses += 1
        logger.info(f"Cache miss for URL: {url}")

    def record_error(self, error: Exception, url: str) -> None:
        """エラーを記録"""
        self.errors.append({
            'error_type': type(error).__name__,
            'message': str(error),
            'url': url,
            'timestamp': datetime.now()
        })
        logger.error(f"Error recorded for {url}: {error}")

    def get_summary(self) -> Dict[str, Any]:
        """パフォーマンス指標のサマリーを取得"""
        if not self.start_time:
            return {
                'status': 'Not started',
                'total_requests': 0,
                'cache_hits': 0,
                'cache_misses': 0,
                'errors': []
            }

        duration = (self.end_time or datetime.now()) - self.start_time
        avg_request_time = (
            sum(r['duration'] for r in self.request_times) / len(self.request_times)
            if self.request_times else 0
        )

        return {
            'status': 'Completed' if self.end_time else 'In progress',
            'duration_seconds': duration.total_seconds(),
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'average_request_time': avg_request_time,
            'error_count': len(self.errors),
            'last_errors': self.errors[-5:] if self.errors else []
        }

    @contextmanager
    def measure_request(self, url: str) -> ContextManager[None]:
        """リクエストの実行時間を計測するコンテキストマネージャー"""
        start = time.time()
        success = True
        try:
            yield
        except Exception:
            success = False
            raise
        finally:
            duration = time.time() - start
            self.record_request(url, duration, success)

# グローバルなパフォーマンストラッカー
performance_tracker = PerformanceTracker()

class CacheManager:
    """キャッシュを管理するクラス"""
    def __init__(self, cache_dir: str = "cache", cache_duration: int = CACHE_DURATION):
        self.cache_dir = Path(cache_dir)
        self.cache_duration = cache_duration
        self.cache_dir.mkdir(exist_ok=True)

    def _get_cache_path(self, url: str) -> Path:
        """URLからキャッシュファイルのパスを生成"""
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return self.cache_dir / f"{url_hash}.json"

    def _is_cache_valid(self, cache_path: Path) -> bool:
        """キャッシュが有効かどうかを確認"""
        try:
            if not cache_path.exists():
                return False
            
            mtime = cache_path.stat().st_mtime
            age = time.time() - mtime
            return age < self.cache_duration
            
        except Exception as e:
            logger.error(f"Error checking cache validity: {e}")
            return False

    def get_cached_data(self, url: str) -> Optional[List[Dict[str, Any]]]:
        """URLに対応するキャッシュデータを取得"""
        cache_path = self._get_cache_path(url)
        
        if not self._is_cache_valid(cache_path):
            return None
            
        try:
            with cache_path.open('r', encoding='utf-8') as f:
                data = json.load(f)
                # Convert ISO format strings back to datetime objects
                for item in data:
                    if 'timestamp' in item:
                        item['timestamp'] = datetime.fromisoformat(item['timestamp'])
                logger.info(f"Successfully read from cache: {url}")
                return data
                
        except Exception as e:
            logger.error(f"Error reading from cache: {e}")
            return None

    def save_to_cache(self, url: str, data: List[Dict[str, Any]]) -> None:
        """データをキャッシュに保存"""
        cache_path = self._get_cache_path(url)
        temp_path = cache_path.with_suffix('.tmp')
        
        try:
            # Convert datetime objects to ISO format strings
            serializable_data = []
            for item in data:
                item_copy = item.copy()
                if 'timestamp' in item_copy:
                    item_copy['timestamp'] = item_copy['timestamp'].isoformat()
                serializable_data.append(item_copy)
            
            # Write to temporary file first
            with temp_path.open('w', encoding='utf-8') as f:
                json.dump(serializable_data, f, ensure_ascii=False, indent=2)
            
            # Atomic replace
            temp_path.replace(cache_path)
            logger.info(f"Successfully cached data for: {url}")
            
        except Exception as e:
            logger.error(f"Error saving to cache: {e}")
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            raise CacheError(f"Failed to save data to cache: {e}")

    def clear_cache(self) -> None:
        """キャッシュディレクトリ内のすべてのファイルを削除"""
        try:
            for cache_file in self.cache_dir.glob('*.json'):
                try:
                    cache_file.unlink()
                except Exception as e:
                    logger.warning(f"Failed to delete cache file {cache_file}: {e}")
            logger.info("Cache cleared successfully")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            raise CacheError(f"Failed to clear cache: {e}")

# グローバルなキャッシュマネージャー
cache_manager = CacheManager()

class ErrorHandler:
    """エラーハンドリングクラス"""
    def __init__(self):
        self.errors = []  # List[ScraperError]
        self.error_counts = {severity: 0 for severity in ErrorSeverity}
        self.consecutive_high_severity_errors = 0
        self.max_consecutive_high_severity_errors = 3

    def handle_error(self, error: ScraperError) -> None:
        """エラーを処理し、ログに記録"""
        self.errors.append(error)
        self.error_counts[error.severity] += 1

        # Update consecutive high severity error count
        if error.severity == ErrorSeverity.HIGH:
            self.consecutive_high_severity_errors += 1
        else:
            self.consecutive_high_severity_errors = 0

        # Log the error
        log_data = {
            "error_id": error.error_id,
            "severity": error.severity.value,
            "message": str(error),
            "timestamp": error.timestamp.isoformat(),
            "context": error.context
        }
        logger.error(json.dumps(log_data))

        # Handle critical errors
        if error.severity == ErrorSeverity.HIGH:
            logger.error(f"Critical error occurred: {error}")
            if self.consecutive_high_severity_errors >= self.max_consecutive_high_severity_errors:
                raise ScraperError("Too many consecutive high severity errors")
        elif error.severity == ErrorSeverity.MEDIUM:
            logger.warning(f"Warning: {error}")
        else:
            logger.info(f"Minor error: {error}")

    def get_error_summary(self) -> Dict[str, Any]:
        """エラーサマリーを取得"""
        return {
            'errors': {
                'total_errors': len(self.errors),
                'error_counts': {severity.value: count for severity, count in self.error_counts.items()},
                'recent_errors': [
                    {
                        'error_id': error.error_id,
                        'severity': error.severity.value,
                        'message': str(error),
                        'timestamp': error.timestamp.isoformat(),
                        'context': error.context
                    }
                    for error in self.errors[-10:]  # 最新の10件のエラーを返す
                ]
            }
        }

    def get_consecutive_high_severity_errors(self) -> int:
        """連続した重大なエラーの数を取得"""
        return self.consecutive_high_severity_errors

    def should_continue(self) -> bool:
        """スクレイピングを続行すべきかを判断"""
        return self.consecutive_high_severity_errors < self.max_consecutive_high_severity_errors

# グローバルなエラーハンドラー
error_handler = ErrorHandler()

def validate_price_data(data: Dict[str, Any]) -> bool:
    """
    Validate price data to ensure all required fields are present and correctly formatted.
    
    Args:
        data: Dictionary containing price data
        
    Returns:
        bool: True if validation passes, False otherwise
        
    Raises:
        ValidationError: If validation fails
    """
    required_fields = ['model', 'price', 'source']
    for field in required_fields:
        if field not in data:
            raise ValidationError(f"Missing required field: {field}")
            
    if not isinstance(data['model'], str):
        raise ValidationError("Model must be a string")
        
    if not isinstance(data['price'], (int, float)):
        raise ValidationError("Price must be a number")
        
    if data['price'] <= 0:
        raise ValidationError("Price must be positive")
        
    if not isinstance(data['source'], str):
        raise ValidationError("Source must be a string")
        
    return True

class Scraper:
    """スクレイピングを実行するクラス"""
    def __init__(self, config=None):
        self.config = self._load_default_config()
        if config:
            self.config.update(config)
        self.session = requests.Session()
        self.session.headers.update(self.config.get('headers', {}))
        self.error_handler = ErrorHandler()
        self.performance_tracker = PerformanceTracker()
        self.cache_manager = CacheManager()
        self.performance_metrics = {
            'start_time': None,
            'end_time': None,
            'total_duration': None,
            'request_durations': {},
            'cache_hits': {},
            'cache_misses': {}
        }

    def measure_request(self, url: str, start_time: float) -> None:
        """リクエストの測定を行う"""
        end_time = time.time()
        duration = end_time - start_time
        success = True  # デフォルトはTrue、エラー時にFalseに設定
        try:
            self.performance_tracker.record_request(url, duration, success)
            if url not in self.performance_metrics['request_durations']:
                self.performance_metrics['request_durations'][url] = []
            self.performance_metrics['request_durations'][url].append(duration)
        except Exception as e:
            logger.error(f"Failed to record request metrics: {str(e)}")

    def record_cache_hit(self, url: str) -> None:
        """キャッシュヒットを記録"""
        self.performance_tracker.record_cache_hit(url)
        if url not in self.performance_metrics['cache_hits']:
            self.performance_metrics['cache_hits'][url] = 0
        self.performance_metrics['cache_hits'][url] += 1

    def record_cache_miss(self, url: str) -> None:
        """キャッシュミスを記録"""
        self.performance_tracker.record_cache_miss(url)
        if url not in self.performance_metrics['cache_misses']:
            self.performance_metrics['cache_misses'][url] = 0
        self.performance_metrics['cache_misses'][url] += 1

    def start_scraping(self) -> None:
        """スクレイピング開始時の処理"""
        self.performance_tracker.start_scraping()
        self.performance_metrics['start_time'] = time.time()

    def end_scraping(self) -> None:
        """スクレイピング終了時の処理"""
        self.performance_tracker.end_scraping()
        self.performance_metrics['end_time'] = time.time()
        if self.performance_metrics['start_time']:
            self.performance_metrics['total_duration'] = self.performance_metrics['end_time'] - self.performance_metrics['start_time']

    def scrape_url(self, url: str, source: str = None) -> List[Dict[str, Any]]:
        """
        URLをスクレイピングして価格データを取得する
        
        Args:
            url: スクレイピング対象のURL
            source: データソース（'kaitori'または'official'）
            
        Returns:
            List[Dict[str, Any]]: 価格データのリスト
        """
        if source is None:
            source = 'unknown'

        try:
            # キャッシュをチェック
            cached_data = self.cache_manager.get_cached_data(url)
            if cached_data:
                self.record_cache_hit(url)
                return cached_data
                
            self.record_cache_miss(url)
            
            # リクエストを実行
            start_time = time.time()
            response = self.session.get(url, timeout=self.config.get('timeout', 30))
            response.raise_for_status()
            self.measure_request(url, start_time)
            
            # レスポンスをパース
            data = self._parse_response(response.text, source)
            
            # キャッシュに保存
            self.cache_manager.save_to_cache(url, data)
            
            return data
        except requests.exceptions.RequestException as e:
            self.error_handler.handle_error(HTTPError(f"Request failed: {str(e)}", url=url))
            raise
        except Exception as e:
            self.error_handler.handle_error(ScraperError(f"Scraping failed: {str(e)}"))
            raise

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

    def get_kaitori_prices(self) -> List[Dict[str, Any]]:
        """買取価格を取得する"""
        try:
            self.start_scraping()
            prices = []
            for url in self.config.get('urls', {}).get('kaitori', []):
                try:
                    data = self.scrape_url(url, 'kaitori')
                    prices.extend(data)
                except Exception as e:
                    self.error_handler.handle_error(ScraperError(str(e), 'kaitori', url))
                    continue

            return prices
        finally:
            self.end_scraping()

    def get_official_prices(self) -> List[Dict[str, Any]]:
        """公式価格を取得する"""
        try:
            self.start_scraping()
            prices = []
            for url in self.config.get('urls', {}).get('official', []):
                try:
                    data = self.scrape_url(url, 'official')
                    prices.extend(data)
                except Exception as e:
                    self.error_handler.handle_error(ScraperError(str(e), 'official', url))
                    continue

            return prices
        finally:
            self.end_scraping()

    def _parse_response(self, html: str, source: str) -> List[Dict[str, Any]]:
        """HTMLレスポンスをパースする"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            prices = []
            
            # price-itemクラスを持つ要素を検索
            items = soup.find_all(class_='price-item')
            if not items:
                # 旧フォーマットのチェック
                items = soup.find_all(class_='rf-productgrid-item')
            
            for item in items:
                try:
                    # 新フォーマット
                    model = item.find(class_='model')
                    price_elem = item.find(class_='price')
                    condition = item.find(class_='condition')
                    
                    # 旧フォーマットのチェック
                    if not all([model, price_elem, condition]):
                        model = item.find(class_='rf-productgrid-producttitle')
                        price_elem = item.find(class_='rf-productgrid-price')
                        condition = item.find(class_='rf-productgrid-condition')
                    
                    if not all([model, price_elem]):
                        continue
                    
                    model_text = model.text.strip()
                    price_text = price_elem.text.strip().replace('¥', '').replace(',', '')
                    condition_text = condition.text.strip() if condition else '新品'
                    
                    price_data = {
                        'model': model_text,
                        'price': float(price_text),
                        'condition': condition_text,
                        'source': source,
                        'timestamp': datetime.now(timezone.utc)
                    }
                    
                    if validate_price_data(price_data):
                        prices.append(price_data)
                except (ValueError, AttributeError) as e:
                    self.error_handler.handle_error(ParseError(str(e), str(item), source))
                    continue
            
            return prices
        except Exception as e:
            self.error_handler.handle_error(ParseError(str(e), html, source))
            return []

    def _load_default_config(self) -> Dict[str, Any]:
        """デフォルト設定を読み込む"""
        return {
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            },
            'selectors': {
                'price_item': '.price-item',
                'model': '.model',
                'price': '.price',
                'condition': '.condition'
            },
            'timeout': 30,
            'max_retries': 3
        }

    def get_summary(self) -> Dict[str, Any]:
        return {
            'performance': self.performance_tracker.get_summary(),
            'errors': self.error_handler.get_error_summary()
        }