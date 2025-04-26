import concurrent.futures
import json
import logging
import os
import re
import time
import uuid
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
    price: int
    source: str
    timestamp: datetime = Field(default_factory=datetime.now)
    url: Optional[str] = None
    condition: Optional[str] = None
    notes: Optional[str] = None
    currency: str = "JPY"

    def to_dict(self) -> Dict[str, Any]:
        """JSONシリアライズ可能な辞書に変換"""
        data = self.dict()
        data['timestamp'] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PriceData':
        """辞書からPriceDataオブジェクトを作成"""
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

    @field_validator('price')
    @classmethod
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError("Price must be positive")
        if v > 1000000:  # 100万円以上の価格は異常値として扱う
            raise ValueError("Price seems too high")
        return v
    
    @field_validator('model')
    @classmethod
    def validate_model(cls, v):
        # iPhoneモデルの正規表現パターン
        model_pattern = r'^iPhone (?:SE|1[0-5])(?: Pro| Pro Max)? \d{1,3}(?:GB|TB)$'
        if not re.match(model_pattern, v):
            raise ValueError(f"Invalid model format: {v}. Expected format: iPhone [model] [capacity]")
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
    def __init__(self, cache_dir: str = "cache", cache_duration: int = CACHE_DURATION):
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
    
    def get_cached_data(self, url: str) -> Optional[List[PriceData]]:
        """キャッシュからデータを取得"""
        cache_path = self._get_cache_path(url)
        
        if not self._is_cache_valid(cache_path):
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"Cache hit for {url}")
                return [PriceData.from_dict(item) for item in data]
        except Exception as e:
            logger.warning(f"Failed to read cache for {url}: {str(e)}")
            return None
    
    def save_to_cache(self, url: str, data: List[PriceData]) -> None:
        """データをキャッシュに保存"""
        cache_path = self._get_cache_path(url)
        
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump([price.to_dict() for price in data], f, ensure_ascii=False, indent=2)
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
        self.consecutive_high_severity_errors = 0
    
    def handle_error(self, error: ScraperError) -> None:
        """エラーを処理し、記録する"""
        self.errors.append(error)
        self.error_counts[error.severity] += 1
        
        # エラーの重大度に応じた処理
        if error.severity == ErrorSeverity.HIGH:
            self.consecutive_high_severity_errors += 1
            logger.error(f"Critical error occurred: {error}")
        elif error.severity == ErrorSeverity.MEDIUM:
            self.consecutive_high_severity_errors = 0
            logger.warning(f"Warning: {error}")
        else:
            self.consecutive_high_severity_errors = 0
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
    
    def get_consecutive_high_severity_errors(self) -> int:
        """連続して発生した重大なエラーの数を返す"""
        return self.consecutive_high_severity_errors
    
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

class Scraper:
    def __init__(self):
        self.config = self._load_config()
        self.headers = {
            'User-Agent': self.config['scraper']['user_agent'],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        self.cache_manager = CacheManager()
        self.error_handler = ErrorHandler()
        self.performance_tracker = PerformanceTracker()
        
    def _load_config(self) -> Dict[str, Any]:
        """設定ファイルを読み込む"""
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
        
    def _handle_error(self, error: Exception, url: str = "unknown", severity: ErrorSeverity = ErrorSeverity.MEDIUM) -> None:
        """エラーハンドリングの共通処理"""
        error_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc)
        context = {
            'url': url,
            'timestamp': timestamp.isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error)
        }
        
        if isinstance(error, HTTPError):
            severity = ErrorSeverity.HIGH
            context['status_code'] = error.status_code
        elif isinstance(error, ParseError):
            severity = ErrorSeverity.MEDIUM
            context['html_snippet'] = error.html_snippet
        elif isinstance(error, ValidationError):
            severity = ErrorSeverity.LOW
            context['invalid_data'] = error.invalid_data
        elif isinstance(error, CacheError):
            severity = ErrorSeverity.LOW
            context['cache_path'] = error.cache_path
            
        self.error_handler.handle_error(ScraperError(message=str(error), severity=severity, context=context))
        
        # 重大なエラーが連続して発生した場合は例外を発生させる
        if severity == ErrorSeverity.HIGH:
            if self.error_handler.get_consecutive_high_severity_errors() >= 3:
                raise ScraperError("Too many consecutive high severity errors", severity=ErrorSeverity.HIGH)
                
    def scrape_url(self, url: str) -> List[Dict[str, Any]]:
        """URLから価格情報をスクレイピング"""
        try:
            # キャッシュの確認
            cached_data = self.cache_manager.get_cached_data(url)
            if cached_data:
                logger.info(f"キャッシュからデータを取得: {url}")
                return [price.to_dict() for price in cached_data]

            # スクレイピングの実行
            start_time = time.time()
            self.performance_tracker.start_scraping(url)
            
            # HTTPリクエスト
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            # HTMLパース
            soup = BeautifulSoup(response.text, 'html.parser')
            price_items = soup.select(self.config['scraper']['selectors']['price_item'])
            
            if not price_items:
                raise ParseError("No price items found", html_snippet=response.text[:200])
                
            prices = []
            for item in price_items:
                try:
                    model = item.select_one(self.config['scraper']['selectors']['model']).text.strip()
                    price_text = item.select_one(self.config['scraper']['selectors']['price']).text.strip()
                    price = int(price_text.replace(',', ''))
                    condition = item.select_one(self.config['scraper']['selectors']['condition']).text.strip()
                    
                    price_data = PriceData(
                        model=model,
                        price=price,
                        source=url,
                        timestamp=datetime.now(timezone.utc),
                        condition=condition
                    )
                    
                    prices.append(price_data)
                except Exception as e:
                    self._handle_error(e, url, ErrorSeverity.LOW)
                    continue
                    
            if not prices:
                raise ParseError("No valid price data found", html_snippet=response.text[:200])
                
            # キャッシュに保存
            try:
                self.cache_manager.save_to_cache(url, prices)
            except Exception as e:
                self._handle_error(e, url, ErrorSeverity.LOW)
                
            # パフォーマンス計測終了
            self.performance_tracker.end_scraping(
                url=url,
                start_time=start_time,
                success=True,
                items_found=len(prices)
            )
            
            return [price.to_dict() for price in prices]
            
        except requests.exceptions.RequestException as e:
            self._handle_error(HTTPError(str(e), url=url, status_code=getattr(e.response, 'status_code', None)))
            return []
        except Exception as e:
            self._handle_error(e, url)
            return []
            
    def get_summary(self) -> Dict[str, Any]:
        """パフォーマンスとエラーのサマリーを取得"""
        return {
            'performance': self.performance_tracker.get_summary(),
            'errors': self.error_handler.get_error_summary()
        }

    def get_kaitori_prices(self) -> List[Dict[str, Any]]:
        """買取価格を取得する"""
        try:
            config = self._load_config()
            urls = config['scraper']['kaitori_rudea_urls']
            
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                futures = [executor.submit(self.scrape_url, url) for url in urls]
                results = []
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        if result:
                            results.extend(result)
                    except Exception as e:
                        self._handle_error(e, "Unknown URL", ErrorSeverity.HIGH)
                
                return results
                
        except Exception as e:
            self._handle_error(e, "get_kaitori_prices", ErrorSeverity.HIGH)
            return []

    def get_official_prices(self) -> List[Dict[str, Any]]:
        """公式価格を取得する"""
        try:
            config = self._load_config()
            urls = config['scraper']['official_urls']
            
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                futures = [executor.submit(self.scrape_url, url) for url in urls]
                results = []
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        if result:
                            results.extend(result)
                    except Exception as e:
                        self._handle_error(e, "Unknown URL", ErrorSeverity.HIGH)
                
                return results
                
        except Exception as e:
            self._handle_error(e, "get_official_prices", ErrorSeverity.HIGH)
            return []