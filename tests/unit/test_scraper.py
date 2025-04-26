import os
import sys
import time
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# プロジェクトのルートディレクトリをPythonパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.lambda_functions.get_prices_lambda.scraper import (
    MAX_WORKERS, TIMEOUT, CacheError, CacheManager, ErrorHandler,
    ErrorSeverity, HTTPError, ParseError, PerformanceMetrics,
    PerformanceTracker, PriceData, ScraperError, ValidationError,
    get_kaitori_prices, get_official_prices, scrape_url, validate_price_data)


@pytest.fixture
def mock_response():
    response = MagicMock()
    response.text = """
    <div class="price">¥120,000</div>
    <div class="model">iPhone 15 128GB</div>
    """
    return response

def test_get_kaitori_prices_success(mock_response):
    with patch('requests.get', return_value=mock_response):
        prices = get_kaitori_prices()
        assert len(prices) > 0
        assert isinstance(prices[0], PriceData)

def test_get_kaitori_prices_retry():
    with patch('requests.get', side_effect=Exception("Connection error")):
        with pytest.raises(ScraperError) as exc_info:
            get_kaitori_prices()
        assert "Failed to scrape" in str(exc_info.value)

def test_price_data_validation():
    valid_data = {
        'model': 'iPhone 15 128GB',
        'price': '120000',
        'source': 'test_source',
        'timestamp': datetime.now(timezone.utc)
    }
    price_data = PriceData(**valid_data)
    assert price_data.price == 120000.00
    assert price_data.currency == "JPY"

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
def mock_config():
    return {
        'scraper': {
            'user_agent': 'test-agent',
            'request_timeout': 10,
            'kaitori_rudea_urls': [
                'https://example.com/url1',
                'https://example.com/url2',
                'https://example.com/url3'
            ],
            'apple_store_url': 'https://example.com/apple'
        }
    }

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
    with patch('src.lambda_functions.get_prices_lambda.scraper.load_config', return_value=mock_config), \
         patch('src.lambda_functions.get_prices_lambda.scraper.safe_request') as mock_request:
        
        # モックレスポンスの設定
        mock_response = MagicMock()
        mock_response.text = mock_html_response
        mock_request.return_value = mock_response
        
        # 関数の実行
        prices = get_official_prices()
        
        # 結果の検証
        assert len(prices) == 2
        assert prices[0].model == "iPhone 15 Pro 256GB"
        assert prices[0].price == 150000
        assert prices[0].condition == "新品"
        assert prices[1].model == "iPhone 15 128GB"
        assert prices[1].price == 120000
        assert prices[1].condition == "新品"

def test_get_official_prices_no_elements(mock_config):
    with patch('src.lambda_functions.get_prices_lambda.scraper.load_config', return_value=mock_config), \
         patch('src.lambda_functions.get_prices_lambda.scraper.safe_request') as mock_request:
        
        # 空のHTMLレスポンス
        mock_response = MagicMock()
        mock_response.text = "<html><body></body></html>"
        mock_request.return_value = mock_response
        
        # 関数の実行
        prices = get_official_prices()
        
        # 結果の検証
        assert len(prices) == 0

def test_get_official_prices_request_error(mock_config):
    with patch('src.lambda_functions.get_prices_lambda.scraper.load_config', return_value=mock_config), \
         patch('src.lambda_functions.get_prices_lambda.scraper.safe_request') as mock_request:
        
        # リクエストエラーをシミュレート
        mock_request.side_effect = HTTPError("Connection failed")
        
        # エラーが発生することを確認
        with pytest.raises(ScraperError) as exc_info:
            get_official_prices()
        
        assert "Failed to scrape Apple Store" in str(exc_info.value)

def test_get_official_prices_invalid_html(mock_config):
    with patch('src.lambda_functions.get_prices_lambda.scraper.load_config', return_value=mock_config), \
         patch('src.lambda_functions.get_prices_lambda.scraper.safe_request') as mock_request:
        
        # 無効なHTMLレスポンス
        mock_response = MagicMock()
        mock_response.text = "<div>Invalid HTML</div>"
        mock_request.return_value = mock_response
        
        # 関数の実行
        prices = get_official_prices()
        
        # 結果の検証
        assert len(prices) == 0

def test_scrape_url_success(mock_config, mock_response):
    """単一URLのスクレイピング成功テスト"""
    with patch('requests.get', return_value=mock_response):
        prices = scrape_url('https://example.com/url1', mock_config)
        
        assert len(prices) == 1
        assert prices[0]['model'] == 'iPhone 15 Pro 256GB'
        assert prices[0]['price'] == '150000'
        assert prices[0]['source'] == 'https://example.com/url1'
        assert prices[0]['condition'] == '新品'

def test_scrape_url_failure(mock_config):
    """単一URLのスクレイピング失敗テスト"""
    with patch('requests.get', side_effect=Exception('Connection error')):
        with pytest.raises(Exception):
            scrape_url('https://example.com/url1', mock_config)

def test_get_kaitori_prices_parallel_success(mock_config, mock_response):
    """並列処理による複数URLのスクレイピング成功テスト"""
    with patch('requests.get', return_value=mock_response):
        prices = get_kaitori_prices()
        
        assert len(prices) == 3  # 3つのURLからそれぞれ1つずつ価格情報を取得
        assert all(price['model'] == 'iPhone 15 Pro 256GB' for price in prices)
        assert all(price['price'] == '150000' for price in prices)

def test_get_kaitori_prices_parallel_partial_failure(mock_config, mock_response):
    """並列処理での一部失敗テスト"""
    def mock_get(url, **kwargs):
        if 'url2' in url:
            raise Exception('Connection error')
        return mock_response
    
    with patch('requests.get', side_effect=mock_get):
        prices = get_kaitori_prices()
        
        # 2つのURLから価格情報を取得（1つは失敗）
        assert len(prices) == 2
        assert all(price['model'] == 'iPhone 15 Pro 256GB' for price in prices)
        assert all(price['price'] == '150000' for price in prices)

def test_get_kaitori_prices_timeout(mock_config, mock_response):
    """タイムアウトテスト"""
    def slow_response(url, **kwargs):
        import time
        time.sleep(TIMEOUT + 1)
        return mock_response
    
    with patch('requests.get', side_effect=slow_response):
        prices = get_kaitori_prices()
        assert len(prices) == 0  # タイムアウトにより価格情報を取得できない

def test_get_kaitori_prices_max_workers(mock_config, mock_response):
    """最大ワーカー数テスト"""
    with patch('requests.get', return_value=mock_response):
        with patch('concurrent.futures.ThreadPoolExecutor') as mock_executor:
            mock_executor.return_value.__enter__.return_value._max_workers = MAX_WORKERS
            get_kaitori_prices()
            
            # ThreadPoolExecutorが正しいmax_workersで作成されたことを確認
            mock_executor.assert_called_once_with(max_workers=MAX_WORKERS)

def test_get_official_prices_success(mock_config, mock_response):
    """公式価格の取得テスト（並列処理なし）"""
    with patch('requests.get', return_value=mock_response):
        prices = get_official_prices()
        
        assert len(prices) == 1
        assert prices[0]['model'] == 'iPhone 15 Pro 256GB'
        assert prices[0]['price'] == '150000'
        assert prices[0]['source'] == mock_config['scraper']['apple_store_url']
        assert prices[0]['condition'] == '新品'

def test_performance_metrics_initialization():
    """PerformanceMetricsの初期化テスト"""
    metrics = PerformanceMetrics(
        url="https://example.com",
        start_time=1.0,
        end_time=2.0,
        response_time=1.0,
        success=True,
        items_found=5
    )
    
    assert metrics.url == "https://example.com"
    assert metrics.start_time == 1.0
    assert metrics.end_time == 2.0
    assert metrics.response_time == 1.0
    assert metrics.success is True
    assert metrics.items_found == 5
    assert metrics.error_message is None

def test_performance_tracker_initialization():
    """PerformanceTrackerの初期化テスト"""
    tracker = PerformanceTracker()
    assert len(tracker.metrics) == 0
    assert tracker._start_time > 0

def test_performance_tracker_start_scraping():
    """スクレイピング開始時のタイムスタンプ記録テスト"""
    tracker = PerformanceTracker()
    start_time = tracker.start_scraping("https://example.com")
    assert isinstance(start_time, float)
    assert start_time > 0

def test_performance_tracker_end_scraping():
    """スクレイピング終了時のメトリクス記録テスト"""
    tracker = PerformanceTracker()
    start_time = time.time()
    time.sleep(0.1)  # 少し待機してレスポンス時間を生成
    tracker.end_scraping(
        url="https://example.com",
        start_time=start_time,
        success=True,
        items_found=3
    )
    
    assert len(tracker.metrics) == 1
    metrics = tracker.metrics[0]
    assert metrics.url == "https://example.com"
    assert metrics.success is True
    assert metrics.items_found == 3
    assert metrics.response_time > 0

def test_performance_tracker_get_summary():
    """パフォーマンスサマリーの計算テスト"""
    tracker = PerformanceTracker()
    
    # 複数のメトリクスを追加
    for i in range(3):
        start_time = time.time()
        time.sleep(0.1)
        tracker.end_scraping(
            url=f"https://example.com/{i}",
            start_time=start_time,
            success=True,
            items_found=i+1
        )
    
    summary = tracker.get_summary()
    assert summary['total_requests'] == 3
    assert summary['success_rate'] == 100.0
    assert summary['total_items_found'] == 6  # 1+2+3
    assert summary['avg_response_time'] > 0
    assert summary['median_response_time'] > 0
    assert summary['std_dev_response_time'] >= 0
    assert summary['min_response_time'] > 0
    assert summary['max_response_time'] > 0
    assert summary['total_execution_time'] > 0

def test_performance_tracker_with_failures():
    """失敗を含むパフォーマンスメトリクスのテスト"""
    tracker = PerformanceTracker()
    
    # 成功と失敗のメトリクスを追加
    start_time = time.time()
    tracker.end_scraping(
        url="https://example.com/success",
        start_time=start_time,
        success=True,
        items_found=2
    )
    
    start_time = time.time()
    tracker.end_scraping(
        url="https://example.com/failure",
        start_time=start_time,
        success=False,
        error_message="Connection error",
        items_found=0
    )
    
    summary = tracker.get_summary()
    assert summary['total_requests'] == 2
    assert summary['success_rate'] == 50.0
    assert summary['total_items_found'] == 2

def test_scrape_url_performance_tracking(mock_config, mock_response):
    """スクレイピング関数のパフォーマンス計測テスト"""
    with patch('requests.get', return_value=mock_response):
        prices = scrape_url('https://example.com/url1', mock_config)
        
        # パフォーマンスメトリクスが記録されていることを確認
        assert len(performance_tracker.metrics) > 0
        metrics = performance_tracker.metrics[-1]
        assert metrics.url == 'https://example.com/url1'
        assert metrics.success is True
        assert metrics.items_found == len(prices)

def test_get_kaitori_prices_performance_tracking(mock_config, mock_response):
    """並列スクレイピングのパフォーマンス計測テスト"""
    with patch('requests.get', return_value=mock_response):
        prices = get_kaitori_prices()
        
        # パフォーマンスサマリーが出力されていることを確認
        summary = performance_tracker.get_summary()
        assert summary['total_requests'] == len(mock_config['scraper']['kaitori_rudea_urls'])
        assert summary['success_rate'] == 100.0
        assert summary['total_items_found'] == len(prices)

def test_cache_manager_initialization():
    """CacheManagerの初期化テスト"""
    cache_manager = CacheManager(cache_dir="test_cache", cache_duration=60)
    assert cache_manager.cache_dir.name == "test_cache"
    assert cache_manager.cache_duration == 60
    assert cache_manager.cache_dir.exists()

def test_cache_path_generation():
    """キャッシュファイルパスの生成テスト"""
    cache_manager = CacheManager()
    url = "https://example.com/test/page"
    cache_path = cache_manager._get_cache_path(url)
    assert cache_path.name == "https___example.com_test_page.json"

def test_cache_validity():
    """キャッシュの有効期限テスト"""
    cache_manager = CacheManager(cache_duration=1)  # 1秒の有効期限
    url = "https://example.com/test"
    cache_path = cache_manager._get_cache_path(url)
    
    # キャッシュを作成
    test_data = [{"model": "iPhone 15", "price": "100000"}]
    cache_manager.save_to_cache(url, test_data)
    
    # 有効期限内のテスト
    assert cache_manager._is_cache_valid(cache_path) is True
    
    # 有効期限切れのテスト
    time.sleep(2)
    assert cache_manager._is_cache_valid(cache_path) is False

def test_cache_save_and_retrieve():
    """キャッシュの保存と取得テスト"""
    cache_manager = CacheManager()
    url = "https://example.com/test"
    test_data = [{"model": "iPhone 15", "price": "100000"}]
    
    # キャッシュに保存
    cache_manager.save_to_cache(url, test_data)
    
    # キャッシュから取得
    retrieved_data = cache_manager.get_cached_data(url)
    assert retrieved_data == test_data

def test_cache_clear():
    """キャッシュのクリアテスト"""
    cache_manager = CacheManager()
    url = "https://example.com/test"
    test_data = [{"model": "iPhone 15", "price": "100000"}]
    
    # キャッシュを作成
    cache_manager.save_to_cache(url, test_data)
    assert len(list(cache_manager.cache_dir.glob("*.json"))) == 1
    
    # キャッシュをクリア
    cache_manager.clear_cache()
    assert len(list(cache_manager.cache_dir.glob("*.json"))) == 0

def test_scrape_url_with_cache(mock_config, mock_response):
    """キャッシュを使用したスクレイピングテスト"""
    cache_manager = CacheManager()
    url = "https://example.com/test"
    test_data = [{"model": "iPhone 15", "price": "100000"}]
    
    # キャッシュを作成
    cache_manager.save_to_cache(url, test_data)
    
    # スクレイピング関数を実行（キャッシュが使用されるはず）
    with patch('requests.get', return_value=mock_response) as mock_get:
        prices = scrape_url(url, mock_config)
        # キャッシュが使用されたため、requests.getは呼び出されない
        mock_get.assert_not_called()
        assert prices == test_data

def test_scrape_url_with_expired_cache(mock_config, mock_response):
    """期限切れキャッシュを使用したスクレイピングテスト"""
    cache_manager = CacheManager(cache_duration=1)  # 1秒の有効期限
    url = "https://example.com/test"
    test_data = [{"model": "iPhone 15", "price": "100000"}]
    
    # キャッシュを作成
    cache_manager.save_to_cache(url, test_data)
    
    # キャッシュを期限切れにする
    time.sleep(2)
    
    # スクレイピング関数を実行（キャッシュが期限切れのため、新しいデータを取得）
    with patch('requests.get', return_value=mock_response) as mock_get:
        prices = scrape_url(url, mock_config)
        # キャッシュが期限切れのため、requests.getが呼び出される
        mock_get.assert_called_once()
        assert prices != test_data  # 新しいデータが取得される

def test_cache_error_handling():
    """キャッシュのエラーハンドリングテスト"""
    cache_manager = CacheManager()
    url = "https://example.com/test"
    
    # 無効なJSONデータでキャッシュファイルを作成
    cache_path = cache_manager._get_cache_path(url)
    with open(cache_path, 'w') as f:
        f.write("invalid json")
    
    # エラーが発生してもNoneが返されることを確認
    assert cache_manager.get_cached_data(url) is None

def test_performance_tracker_with_timeout():
    """タイムアウトを含むパフォーマンスメトリクスのテスト"""
    tracker = PerformanceTracker()
    
    start_time = time.time()
    tracker.end_scraping(
        url="https://example.com/timeout",
        start_time=start_time,
        success=False,
        error_message="Request timeout",
        items_found=0
    )
    
    summary = tracker.get_summary()
    assert summary['total_requests'] == 1
    assert summary['success_rate'] == 0.0
    assert summary['total_items_found'] == 0

def test_performance_tracker_with_partial_success():
    """部分的な成功を含むパフォーマンスメトリクスのテスト"""
    tracker = PerformanceTracker()
    
    # 成功と部分的な成功のメトリクスを追加
    start_time = time.time()
    tracker.end_scraping(
        url="https://example.com/success",
        start_time=start_time,
        success=True,
        items_found=5
    )
    
    start_time = time.time()
    tracker.end_scraping(
        url="https://example.com/partial",
        start_time=start_time,
        success=True,
        items_found=2
    )
    
    summary = tracker.get_summary()
    assert summary['total_requests'] == 2
    assert summary['success_rate'] == 100.0
    assert summary['total_items_found'] == 7

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
    """ErrorHandlerのサマリー生成テスト"""
    handler = ErrorHandler()
    
    # エラーを追加
    handler.handle_error(ValidationError("Test error 1"))
    handler.handle_error(ParseError("Test error 2"))
    
    summary = handler.get_error_summary()
    assert summary["total_errors"] == 2
    assert summary["error_counts"]["LOW"] == 1
    assert summary["error_counts"]["MEDIUM"] == 1
    assert len(summary["recent_errors"]) == 2

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

def test_validate_price_data_success():
    """価格データの検証成功テスト"""
    valid_data = {
        'model': 'iPhone 15 128GB',
        'price': '120000',
        'source': 'https://example.com'
    }
    validate_price_data(valid_data)  # 例外が発生しないことを確認

def test_validate_price_data_missing_model():
    """モデル名が欠落している場合の検証テスト"""
    invalid_data = {
        'price': '120000',
        'source': 'https://example.com'
    }
    with pytest.raises(ValidationError) as exc_info:
        validate_price_data(invalid_data)
    assert exc_info.value.context["field"] == "model"

def test_validate_price_data_invalid_price():
    """無効な価格の場合の検証テスト"""
    invalid_data = {
        'model': 'iPhone 15 128GB',
        'price': '-1000',
        'source': 'https://example.com'
    }
    with pytest.raises(ValidationError) as exc_info:
        validate_price_data(invalid_data)
    assert exc_info.value.context["field"] == "price"

def test_validate_price_data_too_high_price():
    """価格が高すぎる場合の検証テスト"""
    invalid_data = {
        'model': 'iPhone 15 128GB',
        'price': '2000000',
        'source': 'https://example.com'
    }
    with pytest.raises(ValidationError) as exc_info:
        validate_price_data(invalid_data)
    assert exc_info.value.context["field"] == "price"

def test_validate_price_data_missing_source():
    """ソースURLが欠落している場合の検証テスト"""
    invalid_data = {
        'model': 'iPhone 15 128GB',
        'price': '120000'
    }
    with pytest.raises(ValidationError) as exc_info:
        validate_price_data(invalid_data)
    assert exc_info.value.context["field"] == "source"

def test_scrape_url_error_handling(mock_config, mock_response):
    """スクレイピング時のエラーハンドリングテスト"""
    with patch('requests.get', side_effect=Exception("Test error")):
        prices = scrape_url('https://example.com/url1', mock_config)
        assert len(prices) == 0  # エラー時は空のリストを返す

def test_scrape_url_parse_error_handling(mock_config, mock_response):
    """パースエラーのハンドリングテスト"""
    mock_response.text = "<div>Invalid HTML</div>"
    with patch('requests.get', return_value=mock_response):
        prices = scrape_url('https://example.com/url1', mock_config)
        assert len(prices) == 0

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