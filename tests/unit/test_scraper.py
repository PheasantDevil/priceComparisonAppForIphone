import json
import os
import sys
import time
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException, Timeout

# プロジェクトのルートディレクトリをPythonパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.lambda_functions.get_prices_lambda.scraper import (
    MAX_WORKERS, TIMEOUT, CacheError, CacheManager, ErrorHandler,
    ErrorSeverity, HTTPError, ParseError, PerformanceMetrics,
    PerformanceTracker, PriceData, Scraper, ScraperError, ValidationError,
    validate_price_data)


# テスト用のフィクスチャ
@pytest.fixture
def mock_response():
    response = Mock()
    response.text = """
    <div class="price-item">
        <div class="model">iPhone 15 Pro</div>
        <div class="price">120000</div>
        <div class="condition">新品</div>
    </div>
    """
    response.status_code = 200
    return response

@pytest.fixture
def mock_config():
    return {
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        },
        'urls': {
            'kaitori': ['https://www.apple.com/jp/shop/buy-iphone'],
            'official': ['https://www.apple.com/jp/shop/buy-iphone']
        },
        'timeout': 30,
        'max_retries': 3,
        'selectors': {
            'condition': '.condition',
            'model': '.model',
            'price': '.price',
            'price_item': '.price-item'
        }
    }

@pytest.fixture
def mock_scraper(mock_config, mock_response):
    """Create a mock Scraper instance with mocked dependencies"""
    scraper = Scraper(config=mock_config)
    scraper.session = MagicMock()
    scraper.session.get.return_value = mock_response
    scraper.cache_manager = MagicMock()
    scraper.cache_manager.get_cached_data.return_value = None
    scraper.error_handler = MagicMock()
    scraper.performance_tracker = MagicMock()
    return scraper

def test_scraper_initialization():
    """Scraperクラスの初期化テスト"""
    scraper = Scraper()
    assert isinstance(scraper.cache_manager, CacheManager)
    assert isinstance(scraper.error_handler, ErrorHandler)
    assert isinstance(scraper.performance_tracker, PerformanceTracker)

def test_get_kaitori_prices(mock_scraper, mock_response):
    """Test getting kaitori prices."""
    with patch('requests.get', return_value=mock_response):
        prices = mock_scraper.get_kaitori_prices()
        assert isinstance(prices, list)
        assert len(prices) > 0
        assert all(isinstance(p, PriceData) for p in prices)
        assert all(p.source == 'kaitori' for p in prices)

def test_get_official_prices(mock_scraper, mock_response):
    """Test getting official prices."""
    with patch('requests.get', return_value=mock_response):
        prices = mock_scraper.get_official_prices()
        assert isinstance(prices, list)
        assert len(prices) > 0
        assert all(isinstance(p, PriceData) for p in prices)
        assert all(p.source == 'official' for p in prices)

def test_scrape_url(mock_scraper, mock_response):
    """Test scraping a single URL"""
    url = "https://example.com"
    source = "kaitori"
    
    result = mock_scraper.scrape_url(url, source)
    
    assert isinstance(result, list)
    assert len(result) > 0
    assert all(isinstance(item, dict) for item in result)
    assert all('model' in item and 'price' in item for item in result)
    mock_scraper.session.get.assert_called_once_with(url, timeout=mock_scraper.config.get('timeout', 30))

def test_scrape_urls(mock_scraper, mock_response):
    """Test scraping multiple URLs in parallel"""
    urls = ["https://example1.com", "https://example2.com"]
    source = "kaitori"
    
    results = mock_scraper.scrape_urls(urls, source)
    
    assert isinstance(results, list)
    assert len(results) == len(urls)
    assert all(isinstance(result, list) for result in results)
    assert mock_scraper.session.get.call_count == len(urls)

def test_parse_response(mock_scraper, mock_response):
    """Test parsing response."""
    with patch('requests.get', return_value=mock_response):
        result = mock_scraper._parse_response(mock_response.text, 'test')
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(item, dict) for item in result)
        assert all('model' in item and 'price' in item for item in result)

def test_measure_request(mock_scraper):
    """Test measuring request duration."""
    start_time = time.time()
    mock_scraper.measure_request('https://example.com', start_time)
    assert isinstance(mock_scraper.performance_metrics['request_durations']['https://example.com'][0], float)

def test_record_cache_hit(mock_scraper):
    """Test recording cache hit."""
    mock_scraper.record_cache_hit('test')
    assert mock_scraper.performance_metrics['cache_hits']['test'] == 1

def test_record_cache_miss(mock_scraper):
    """Test recording cache miss."""
    mock_scraper.record_cache_miss('test')
    assert mock_scraper.performance_metrics['cache_misses']['test'] == 1

def test_start_scraping(mock_scraper):
    """Test starting scraping session."""
    mock_scraper.start_scraping()
    assert mock_scraper.performance_metrics['start_time'] is not None

def test_end_scraping(mock_scraper):
    """Test ending scraping session."""
    mock_scraper.start_scraping()
    mock_scraper.end_scraping()
    assert mock_scraper.performance_metrics['end_time'] is not None
    assert mock_scraper.performance_metrics['total_duration'] is not None

def test_get_kaitori_prices_success(mock_config, mock_response):
    """買取価格取得の成功テスト"""
    scraper = Scraper(mock_config)
    with patch('requests.Session.get', return_value=mock_response):
        prices = scraper.get_kaitori_prices()
        assert len(prices) > 0
        assert isinstance(prices[0], dict)
        assert 'model' in prices[0]
        assert 'price' in prices[0]

def test_get_kaitori_prices_retry(mock_config):
    """買取価格取得のリトライテスト"""
    scraper = Scraper(mock_config)
    with patch('requests.Session.get', side_effect=Exception("Connection error")):
        with pytest.raises(ScraperError) as exc_info:
            scraper.get_kaitori_prices()
        assert "買取価格の取得に失敗" in str(exc_info.value)

def test_price_data_validation():
    valid_data = {
        'model': 'iPhone 15',
        'price': 89800,
        'source': 'https://example.com',
        'timestamp': datetime.now()
    }
    assert validate_price_data(valid_data) is True

    with pytest.raises(ValueError):
        invalid_data = valid_data.copy()
        invalid_data['price'] = -1000
        validate_price_data(invalid_data)

    with pytest.raises(ValueError):
        invalid_data = valid_data.copy()
        invalid_data['source'] = 'not_a_url'
        validate_price_data(invalid_data)

def test_price_data_invalid_model():
    invalid_data = {
        'model': 'Invalid Model',
        'price': '120000',
        'source': 'test_source',
        'timestamp': datetime.now(timezone.utc)
    }
    with pytest.raises(ValueError):
        PriceData(**invalid_data)

@pytest.fixture
def mock_html_response():
    return """
    <div class="as-producttile">
        <span class="as-producttile-title">iPhone 15 Pro 256GB</span>
        <span class="as-price-currentprice">¥150,000</span>
    </div>
    <div class="as-producttile">
        <span class="as-producttile-title">iPhone 15 128GB</span>
        <span class="as-price-currentprice">¥120,000</span>
    </div>
    """

def test_get_official_prices_success(mock_config, mock_html_response):
    """公式価格取得の成功テスト"""
    scraper = Scraper(mock_config)
    with patch('requests.Session.get') as mock_get:
        # モックレスポンスの設定
        mock_response = MagicMock()
        mock_response.text = mock_html_response
        mock_get.return_value = mock_response
        
        # 関数の実行
        prices = scraper.get_official_prices()
        
        # 結果の検証
        assert len(prices) == 2
        assert prices[0]['model'] == "iPhone 15 Pro 256GB"
        assert prices[0]['price'] == 150000.0
        assert prices[0]['condition'] == "新品"
        assert prices[1]['model'] == "iPhone 15 128GB"
        assert prices[1]['price'] == 120000.0
        assert prices[1]['condition'] == "新品"

def test_get_official_prices_no_elements(mock_config):
    """公式価格取得の空要素テスト"""
    scraper = Scraper(mock_config)
    with patch('requests.Session.get') as mock_get:
        # 空のHTMLレスポンス
        mock_response = MagicMock()
        mock_response.text = "<html><body></body></html>"
        mock_get.return_value = mock_response
        
        # 関数の実行
        prices = scraper.get_official_prices()
        
        # 結果の検証
        assert len(prices) == 0

def test_get_official_prices_request_error(mock_config):
    """公式価格取得のリクエストエラーテスト"""
    scraper = Scraper(mock_config)
    with patch('requests.Session.get') as mock_get:
        # リクエストエラーをシミュレート
        mock_get.side_effect = HTTPError("Connection failed")
        
        # エラーが発生することを確認
        with pytest.raises(ScraperError) as exc_info:
            scraper.get_official_prices()
        
        assert "Failed to scrape Apple Store" in str(exc_info.value)

def test_get_official_prices_invalid_html(mock_config):
    """公式価格取得の無効なHTMLテスト"""
    scraper = Scraper(mock_config)
    with patch('requests.Session.get') as mock_get:
        # 無効なHTMLレスポンス
        mock_response = MagicMock()
        mock_response.text = "<div>Invalid HTML</div>"
        mock_get.return_value = mock_response
        
        # 関数の実行
        prices = scraper.get_official_prices()
        
        # 結果の検証
        assert len(prices) == 0

def test_scrape_url_performance_tracking(mock_scraper, mock_response):
    """Test performance tracking during URL scraping."""
    with patch('requests.get', return_value=mock_response):
        mock_scraper.start_scraping()
        result = mock_scraper.scrape_url('https://example.com', 'test')
        mock_scraper.end_scraping()
        
        assert mock_scraper.performance_metrics['start_time'] is not None
        assert mock_scraper.performance_metrics['end_time'] is not None
        assert mock_scraper.performance_metrics['total_duration'] is not None
        assert 'test' in mock_scraper.performance_metrics['request_durations']
        assert mock_scraper.performance_metrics['request_durations']['test'] > 0

def test_error_handling(mock_scraper):
    """Test error handling during scraping."""
    with patch('requests.get', side_effect=RequestException("Connection error")):
        with pytest.raises(HTTPError) as exc_info:
            mock_scraper.scrape_url('https://example.com', 'test')
        assert "Connection error" in str(exc_info.value)

def test_retry_mechanism(mock_scraper):
    """Test retry mechanism for failed requests."""
    mock_response = MagicMock()
    mock_response.text = """
    <div class="price-item">
        <div class="model">iPhone 15 Pro</div>
        <div class="price">120000</div>
        <div class="condition">新品</div>
    </div>
    """
    
    with patch('requests.get', side_effect=[RequestException("Temporary error"), mock_response]):
        result = mock_scraper.scrape_url('https://example.com', 'test')
        assert len(result) > 0

def test_cache_mechanism(mock_scraper, mock_response):
    """Test caching mechanism."""
    url = 'https://example.com'
    
    # First request - should miss cache
    with patch('requests.get', return_value=mock_response):
        result1 = mock_scraper.scrape_url(url, 'test')
        assert mock_scraper.performance_metrics['cache_misses']['test'] == 1
    
    # Second request - should hit cache
    with patch('requests.get', return_value=mock_response):
        result2 = mock_scraper.scrape_url(url, 'test')
        assert mock_scraper.performance_metrics['cache_hits']['test'] == 1
        assert result1 == result2

def test_concurrent_scraping(mock_scraper, mock_response):
    """Test concurrent scraping functionality."""
    urls = ['https://example1.com', 'https://example2.com']
    
    with patch('requests.get', return_value=mock_response):
        results = mock_scraper.scrape_urls(urls, 'test')
        assert len(results) == len(urls)
        assert all(isinstance(result, list) for result in results)
        assert all(len(result) > 0 for result in results)

def test_scrape_url_validation_error_handling(mock_config, mock_response):
    """検証エラーのハンドリングテスト"""
    mock_response.text = """
    <div class="tr">
        <h2>Invalid Model</h2>
        <div class="td2wrap">Invalid Price</div>
    </div>
    """
    with patch('requests.get', return_value=mock_response):
        prices = scrape_url('https://example.com/url1', mock_config)
        assert len(prices) == 0

def test_scrape_url_cache_error_handling(mock_config, mock_response):
    """キャッシュエラーのハンドリングテスト"""
    with patch('requests.get', return_value=mock_response), \
         patch.object(CacheManager, 'save_to_cache', side_effect=Exception("Cache error")):
        prices = scrape_url('https://example.com/url1', mock_config)
        assert len(prices) > 0  # キャッシュエラーでもデータは返す

def test_scrape_url_critical_error_handling(mock_config):
    """重大なエラーの連続発生時のハンドリングテスト"""
    with patch('requests.get', side_effect=HTTPError("Critical error")) as mock_get:
        # 3回連続でエラーを発生させる
        for _ in range(3):
            scrape_url('https://example.com/url1', mock_config)
        
        # 4回目は例外が発生するはず
        with pytest.raises(ScraperError) as exc_info:
            scrape_url('https://example.com/url1', mock_config)
        assert exc_info.value.severity == ErrorSeverity.HIGH

def test_error_severity_enum():
    """ErrorSeverity列挙型のテスト"""
    assert ErrorSeverity.LOW.value == "LOW"
    assert ErrorSeverity.MEDIUM.value == "MEDIUM"
    assert ErrorSeverity.HIGH.value == "HIGH"
    assert len(ErrorSeverity) == 3

def test_scraper_error_initialization():
    """ScraperErrorの初期化テスト"""
    error = ScraperError("Test error", ErrorSeverity.HIGH, {"key": "value"})
    assert str(error) == "Test error"
    assert error.severity == ErrorSeverity.HIGH
    assert error.context == {"key": "value"}
    assert isinstance(error.timestamp, datetime)
    assert error.error_id.startswith("ERR-")

def test_http_error_initialization():
    """HTTPErrorの初期化テスト"""
    error = HTTPError("Connection failed", 404, "https://example.com")
    assert error.severity == ErrorSeverity.HIGH
    assert error.context["status_code"] == 404
    assert error.context["url"] == "https://example.com"

def test_parse_error_initialization():
    """ParseErrorの初期化テスト"""
    html = "<div>test</div>" * 100  # 200文字以上のHTML
    error = ParseError("Parse failed", html, "div.test")
    assert error.severity == ErrorSeverity.MEDIUM
    assert len(error.context["html_snippet"]) == 200
    assert error.context["selector"] == "div.test"

def test_validation_error_initialization():
    """ValidationErrorの初期化テスト"""
    error = ValidationError("Invalid price", "price", 1000000)
    assert error.severity == ErrorSeverity.LOW
    assert error.context["field"] == "price"
    assert error.context["value"] == "1000000"

def test_cache_error_initialization():
    """CacheErrorの初期化テスト"""
    error = CacheError("Cache write failed", "save", Path("/test/cache.json"))
    assert error.severity == ErrorSeverity.LOW
    assert error.context["operation"] == "save"
    assert error.context["cache_path"] == "/test/cache.json"

def test_error_handler_initialization():
    """ErrorHandlerの初期化テスト"""
    handler = ErrorHandler()
    assert len(handler.errors) == 0
    assert handler.error_counts[ErrorSeverity.LOW] == 0
    assert handler.error_counts[ErrorSeverity.MEDIUM] == 0
    assert handler.error_counts[ErrorSeverity.HIGH] == 0

def test_error_handler_handle_error():
    """ErrorHandlerのエラー処理テスト"""
    handler = ErrorHandler()
    
    # 異なる重大度のエラーを追加
    handler.handle_error(ValidationError("Test error 1"))
    handler.handle_error(ParseError("Test error 2"))
    handler.handle_error(HTTPError("Test error 3"))
    
    assert len(handler.errors) == 3
    assert handler.error_counts[ErrorSeverity.LOW] == 1
    assert handler.error_counts[ErrorSeverity.MEDIUM] == 1
    assert handler.error_counts[ErrorSeverity.HIGH] == 1

def test_error_handler_get_summary():
    """Test error summary generation"""
    handler = ErrorHandler()
    handler.handle_error(ValidationError("Test error 1"))
    handler.handle_error(ParseError("Test error 2"))
    
    summary = handler.get_error_summary()
    assert summary['total_errors'] == 2
    assert summary['error_counts']['LOW'] == 1
    assert summary['error_counts']['MEDIUM'] == 1

def test_error_handler_should_continue():
    """ErrorHandlerの継続判断テスト"""
    handler = ErrorHandler()
    
    # HIGHレベルのエラーが2件までは継続可能
    for _ in range(2):
        handler.handle_error(HTTPError("Test error"))
    assert handler.should_continue() is True
    
    # HIGHレベルのエラーが3件以上で中断
    handler.handle_error(HTTPError("Test error"))
    assert handler.should_continue() is False

def test_scraper_consecutive_high_severity_errors():
    """連続した重大なエラーのテスト"""
    scraper = Scraper()
    url = "https://example.com"
    
    # 3回連続でHTTPエラーを発生させる
    with patch('requests.get', side_effect=HTTPError("Connection failed", 500, url)):
        for _ in range(3):
            scraper.scrape_url(url)
            
        # 4回目は例外が発生するはず
        with pytest.raises(ScraperError) as exc_info:
            scraper.scrape_url(url)
        assert exc_info.value.severity == ErrorSeverity.HIGH
        assert "Too many consecutive high severity errors" in str(exc_info.value)
        
def test_scraper_error_context():
    """エラーコンテキストのテスト"""
    scraper = Scraper()
    url = "https://example.com"
    
    # HTTPエラーのコンテキスト
    with patch('requests.get', side_effect=HTTPError("Connection failed", 404, url)):
        scraper.scrape_url(url)
        summary = scraper.get_summary()
        error = summary['errors']['recent_errors'][0]
        assert error['error_type'] == 'HTTPError'
        assert error['context']['status_code'] == 404
        assert error['context']['url'] == url
        
    # パースエラーのコンテキスト
    mock_response = MagicMock()
    mock_response.text = "<div>Invalid HTML</div>" * 100
    with patch('requests.get', return_value=mock_response):
        scraper.scrape_url(url)
        summary = scraper.get_summary()
        error = summary['errors']['recent_errors'][0]
        assert error['error_type'] == 'ParseError'
        assert len(error['context']['html_snippet']) == 200
        
def test_scraper_error_id_generation():
    """エラーIDの生成テスト"""
    scraper = Scraper()
    url = "https://example.com"
    
    with patch('requests.get', side_effect=HTTPError("Connection failed", 404, url)):
        scraper.scrape_url(url)
        summary = scraper.get_summary()
        error = summary['errors']['recent_errors'][0]
        assert 'error_id' in error
        assert isinstance(error['error_id'], str)
        assert len(error['error_id']) > 0
        
def test_scraper_error_timestamp():
    """エラータイムスタンプのテスト"""
    scraper = Scraper()
    url = "https://example.com"
    
    with patch('requests.get', side_effect=HTTPError("Connection failed", 404, url)):
        scraper.scrape_url(url)
        summary = scraper.get_summary()
        error = summary['errors']['recent_errors'][0]
        assert 'timestamp' in error['context']
        assert isinstance(error['context']['timestamp'], str)
        assert datetime.fromisoformat(error['context']['timestamp']).tzinfo is not None 

def test_scraper_performance_metrics():
    """Scraperクラスのパフォーマンスメトリクステスト"""
    scraper = Scraper()
    url = "https://example.com"
    
    # 成功ケースのテスト
    mock_response = MagicMock()
    mock_response.text = """
    <div class="price-item">
        <div class="model">iPhone 15 Pro 256GB</div>
        <div class="price">100,000</div>
        <div class="condition">新品</div>
    </div>
    """
    with patch('requests.get', return_value=mock_response):
        prices = scraper.scrape_url(url)
        summary = scraper.get_summary()
        assert summary['performance']['total_requests'] == 1
        assert summary['performance']['success_rate'] == 100.0
        assert summary['performance']['total_items_found'] == 1
        assert summary['performance']['avg_response_time'] > 0
        assert summary['performance']['min_response_time'] > 0
        assert summary['performance']['max_response_time'] > 0
        
    # 失敗ケースのテスト
    with patch('requests.get', side_effect=HTTPError("Connection failed", 404, url)):
        prices = scraper.scrape_url(url)
        summary = scraper.get_summary()
        assert summary['performance']['total_requests'] == 2
        assert summary['performance']['success_rate'] == 50.0
        assert summary['performance']['total_items_found'] == 1
        assert summary['performance']['error_rate'] == 50.0
        
def test_scraper_performance_metrics_multiple_requests():
    """複数リクエストのパフォーマンスメトリクステスト"""
    scraper = Scraper()
    urls = [
        "https://example.com/1",
        "https://example.com/2",
        "https://example.com/3"
    ]
    
    mock_response = MagicMock()
    mock_response.text = """
    <div class="price-item">
        <div class="model">iPhone 15 Pro 256GB</div>
        <div class="price">100,000</div>
        <div class="condition">新品</div>
    </div>
    """
    
    # 3つのURLに対してスクレイピングを実行
    with patch('requests.get', return_value=mock_response):
        for url in urls:
            scraper.scrape_url(url)
            
        summary = scraper.get_summary()
        assert summary['performance']['total_requests'] == 3
        assert summary['performance']['success_rate'] == 100.0
        assert summary['performance']['total_items_found'] == 3
        assert summary['performance']['avg_response_time'] > 0
        assert summary['performance']['median_response_time'] > 0
        assert summary['performance']['std_dev_response_time'] >= 0
        
def test_scraper_performance_metrics_timeout():
    """タイムアウト時のパフォーマンスメトリクステスト"""
    scraper = Scraper()
    url = "https://example.com"
    
    def slow_response(*args, **kwargs):
        time.sleep(2)  # 2秒待機
        return MagicMock(text="<div>Response</div>")
        
    with patch('requests.get', side_effect=slow_response):
        with pytest.raises(requests.exceptions.Timeout):
            scraper.scrape_url(url)
            
        summary = scraper.get_summary()
        assert summary['performance']['total_requests'] == 1
        assert summary['performance']['success_rate'] == 0.0
        assert summary['performance']['total_items_found'] == 0
        assert summary['performance']['error_rate'] == 100.0
        assert summary['performance']['timeout_rate'] == 100.0
        
def test_scraper_performance_metrics_cache_hit():
    """キャッシュヒット時のパフォーマンスメトリクステスト"""
    scraper = Scraper()
    url = "https://example.com"
    
    # 最初のリクエスト（キャッシュミス）
    mock_response = MagicMock()
    mock_response.text = """
    <div class="price-item">
        <div class="model">iPhone 15 Pro 256GB</div>
        <div class="price">100,000</div>
        <div class="condition">新品</div>
    </div>
    """
    with patch('requests.get', return_value=mock_response):
        scraper.scrape_url(url)
        
    # 2回目のリクエスト（キャッシュヒット）
    with patch('requests.get', return_value=mock_response):
        scraper.scrape_url(url)
        
    summary = scraper.get_summary()
    assert summary['performance']['total_requests'] == 2
    assert summary['performance']['cache_hits'] == 1
    assert summary['performance']['cache_misses'] == 1
    assert summary['performance']['cache_hit_rate'] == 50.0
    
def test_scraper_performance_metrics_parallel_processing():
    """並列処理時のパフォーマンスメトリクステスト"""
    scraper = Scraper()
    urls = [
        "https://example.com/1",
        "https://example.com/2",
        "https://example.com/3"
    ]
    
    mock_response = MagicMock()
    mock_response.text = """
    <div class="price-item">
        <div class="model">iPhone 15 Pro 256GB</div>
        <div class="price">100,000</div>
        <div class="condition">新品</div>
    </div>
    """
    
    # 並列処理で3つのURLをスクレイピング
    with patch('requests.get', return_value=mock_response):
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(scraper.scrape_url, url) for url in urls]
            for future in futures:
                future.result()
                
        summary = scraper.get_summary()
        assert summary['performance']['total_requests'] == 3
        assert summary['performance']['parallel_requests'] == 3
        assert summary['performance']['avg_parallel_workers'] == 3
        assert summary['performance']['total_execution_time'] > 0
        assert summary['performance']['parallel_efficiency'] > 0 

def test_cache_manager_initialization():
    """CacheManagerの初期化テスト"""
    cache_manager = CacheManager()
    assert cache_manager.cache_dir.exists()
    assert cache_manager.cache_duration == 3600  # デフォルトのキャッシュ期間（1時間）
    
    # カスタム設定での初期化
    custom_cache_dir = "test_cache"
    custom_duration = 1800  # 30分
    cache_manager = CacheManager(cache_dir=custom_cache_dir, cache_duration=custom_duration)
    assert cache_manager.cache_dir == Path(custom_cache_dir)
    assert cache_manager.cache_duration == custom_duration
    
def test_cache_path_generation():
    """キャッシュファイルパスの生成テスト"""
    cache_manager = CacheManager()
    url = "https://example.com/path?param=value"
    cache_path = cache_manager._get_cache_path(url)
    
    # URLから安全なファイル名が生成されているか
    assert cache_path.parent == cache_manager.cache_dir
    assert not any(c in cache_path.name for c in '/:?&')  # 特殊文字が除去されている
    assert cache_path.suffix == '.json'
    
def test_cache_validity():
    """キャッシュの有効期限テスト"""
    cache_manager = CacheManager(cache_duration=60)  # 1分のキャッシュ期間
    url = "https://example.com"
    cache_path = cache_manager._get_cache_path(url)
    
    # 有効なキャッシュ
    cache_data = [{'model': 'iPhone 15', 'price': 100000}]
    cache_manager.save_to_cache(url, cache_data)
    assert cache_manager._is_cache_valid(cache_path)
    
    # 期限切れのキャッシュ
    with patch('os.path.getmtime', return_value=time.time() - 120):  # 2分前
        assert not cache_manager._is_cache_valid(cache_path)
        
def test_cache_save_and_retrieve():
    """キャッシュの保存と取得テスト"""
    cache_manager = CacheManager()
    url = "https://example.com"
    test_data = [{
        'model': 'iPhone 15 Pro 256GB',
        'price': 150000,
        'source': url,
        'timestamp': datetime.now(timezone.utc),
        'condition': '新品'
    }]
    
    # データの保存
    cache_manager.save_to_cache(url, test_data)
    assert cache_manager._get_cache_path(url).exists()
    
    # データの取得
    retrieved_data = cache_manager.get_cached_data(url)
    assert retrieved_data == test_data
    
    # 無効なJSONデータのテスト
    with open(cache_manager._get_cache_path(url), 'w') as f:
        f.write('invalid json')
    assert cache_manager.get_cached_data(url) is None
    
def test_cache_clear():
    """キャッシュのクリアテスト"""
    cache_manager = CacheManager()
    urls = [
        "https://example.com/1",
        "https://example.com/2",
        "https://example.com/3"
    ]
    
    # 複数のキャッシュファイルを作成
    for url in urls:
        cache_manager.save_to_cache(url, [{'model': 'iPhone', 'price': 100000}])
        
    # キャッシュのクリア
    cache_manager.clear_cache()
    assert len(list(cache_manager.cache_dir.glob('*.json'))) == 0
    
def test_scrape_url_with_cache():
    """スクレイピング時のキャッシュ使用テスト"""
    scraper = Scraper()
    url = "https://example.com"
    
    # キャッシュにデータを保存
    cache_data = [{
        'model': 'iPhone 15 Pro 256GB',
        'price': 150000,
        'source': url,
        'timestamp': datetime.now(timezone.utc),
        'condition': '新品'
    }]
    scraper.cache_manager.save_to_cache(url, cache_data)
    
    # スクレイピング実行（キャッシュからデータを取得）
    with patch('requests.get') as mock_get:
        prices = scraper.scrape_url(url)
        assert prices == cache_data
        mock_get.assert_not_called()  # HTTPリクエストが行われていないことを確認
        
def test_scrape_url_with_expired_cache():
    """期限切れキャッシュのスクレイピングテスト"""
    scraper = Scraper()
    url = "https://example.com"
    
    # 期限切れのデータをキャッシュに保存
    expired_data = [{
        'model': 'iPhone 15 Pro 256GB',
        'price': 150000,
        'source': url,
        'timestamp': datetime.now(timezone.utc) - timedelta(hours=2),
        'condition': '新品'
    }]
    scraper.cache_manager.save_to_cache(url, expired_data)
    
    # キャッシュを期限切れにする
    with patch('os.path.getmtime', return_value=time.time() - 7200):  # 2時間前
        # 新しいデータをモック
        mock_response = MagicMock()
        mock_response.text = """
        <div class="price-item">
            <div class="model">iPhone 15 Pro 256GB</div>
            <div class="price">150000</div>
            <div class="condition">新品</div>
        </div>
        """
        with patch('requests.get', return_value=mock_response):
            prices = scraper.scrape_url(url)
            assert prices[0]['price'] == 150000  # 新しい価格が取得されていることを確認
            
def test_cache_error_handling():
    """キャッシュエラーのハンドリングテスト"""
    scraper = Scraper()
    url = "https://example.com"
    
    # キャッシュ保存時のエラー
    with patch.object(CacheManager, 'save_to_cache', side_effect=CacheError("Cache write failed", "save", Path("/test/cache.json"))):
        mock_response = MagicMock()
        mock_response.text = """
        <div class="price-item">
            <div class="model">iPhone 15 Pro 256GB</div>
            <div class="price">150000</div>
            <div class="condition">新品</div>
        </div>
        """
        with patch('requests.get', return_value=mock_response):
            prices = scraper.scrape_url(url)
            assert len(prices) > 0  # キャッシュエラーでもデータは返す
            summary = scraper.get_summary()
            assert 'errors' in summary
            assert summary['errors'].get('error_types', {}).get('CacheError', 0) > 0

@patch('requests.get')
def test_scrape_url_success(mock_get, mock_config, mock_response):
    mock_get.return_value = mock_response
    
    scraper = Scraper(mock_config)
    results = scraper.scrape_url(mock_config['urls']['official'][0], mock_config)
    
    assert len(results) == 1
    assert results[0]['model'] == 'iPhone 13 Pro'
    assert results[0]['price'] == 120000.0
    assert results[0]['condition'] == '新品'
    assert results[0]['source'] == mock_config['urls']['official'][0]

@patch('requests.get')
def test_scrape_url_http_error(mock_get, mock_config):
    mock_get.side_effect = RequestException("Connection error")
    
    scraper = Scraper(mock_config)
    with pytest.raises(HTTPError):
        scraper.scrape_url(mock_config['urls']['official'][0], mock_config) 