import json
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from bs4 import BeautifulSoup

from src.lambda_functions.get_prices_lambda.scraper import (CacheError,
                                                            ErrorHandler,
                                                            ErrorSeverity,
                                                            HTTPError,
                                                            ParseError,
                                                            PriceData, Scraper,
                                                            ScraperError,
                                                            ValidationError)

# モックデータ
MOCK_HTML = """
<div class="price-item">
    <div class="model">iPhone 15 Pro</div>
    <div class="price">120000</div>
    <div class="condition">新品</div>
</div>
"""

MOCK_OFFICIAL_HTML = """
<div class="as-producttile">
    <span class="as-producttile-title">iPhone 15 Pro 256GB</span>
    <span class="as-price-currentprice">¥150,000</span>
</div>
"""

@pytest.fixture
def mock_config():
    return {
        'selectors': {
            'price_item': '.price-item',
            'model': '.model',
            'price': '.price',
            'condition': '.condition'
        },
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        },
        'max_retries': 3,
        'timeout': 30,
        'cache_duration': 3600
    }

@pytest.fixture
def mock_response():
    mock = MagicMock()
    mock.text = MOCK_HTML
    mock.status_code = 200
    return mock

@pytest.fixture
def mock_official_response():
    mock = MagicMock()
    mock.text = MOCK_OFFICIAL_HTML
    mock.status_code = 200
    return mock

@pytest.fixture
def scraper(mock_config):
    return Scraper(config=mock_config)

def test_scraper_initialization(scraper, mock_config):
    assert scraper is not None
    assert scraper.config == mock_config
    assert isinstance(scraper.error_handler, ErrorHandler)

@patch('requests.get')
def test_get_kaitori_prices(mock_get, scraper, mock_response):
    mock_get.return_value = mock_response
    prices = scraper.get_kaitori_prices()
    assert len(prices) > 0
    assert all(isinstance(price, PriceData) for price in prices)

@patch('requests.get')
def test_get_official_prices(mock_get, scraper, mock_official_response):
    mock_get.return_value = mock_official_response
    prices = scraper.get_official_prices()
    assert len(prices) > 0
    assert all(isinstance(price, PriceData) for price in prices)

@patch('requests.get')
def test_scrape_url(mock_get, scraper, mock_response):
    mock_get.return_value = mock_response
    url = "https://example.com"
    result = scraper.scrape_url(url, source="test")
    assert result is not None
    assert isinstance(result, list)
    assert all(isinstance(item, PriceData) for item in result)

def test_parse_response(scraper):
    soup = BeautifulSoup(MOCK_HTML, 'html.parser')
    result = scraper._parse_response(MOCK_HTML, source="test")
    assert len(result) > 0
    assert all(isinstance(item, PriceData) for item in result)

def test_measure_request(scraper):
    start_time = datetime.now()
    result = scraper._measure_request("https://example.com")
    assert isinstance(result, float)
    assert result >= 0

def test_record_cache_hit(scraper):
    url = "https://example.com"
    scraper.cache_manager.record_cache_hit(url)
    assert url in scraper.cache_manager.cache_hits

def test_record_cache_miss(scraper):
    url = "https://example.com"
    scraper.cache_manager.record_cache_miss(url)
    assert url in scraper.cache_manager.cache_misses

def test_start_scraping(scraper):
    scraper.start_scraping()
    assert scraper.start_time is not None

def test_end_scraping(scraper):
    scraper.start_scraping()
    result = scraper.end_scraping()
    assert isinstance(result, float)
    assert result >= 0

@patch('requests.get')
def test_scrape_urls(mock_get, scraper, mock_response):
    mock_get.return_value = mock_response
    urls = ["https://example1.com", "https://example2.com"]
    results = scraper.scrape_urls(urls, source="test")
    assert len(results) == len(urls)

def test_price_data_validation():
    data = {
        "model": "iPhone 15 Pro",
        "price": 120000,
        "condition": "新品",
        "source": "https://example.com"
    }
    price_data = PriceData(**data)
    assert price_data.model == data["model"]
    assert price_data.price == data["price"]
    assert price_data.condition == data["condition"]
    assert price_data.source == data["source"]

def test_price_data_invalid_model():
    with pytest.raises(ValueError):
        PriceData(
            model="Invalid Model",
            price=120000,
            condition="新品",
            source="https://example.com"
        )

@patch('requests.get')
def test_get_kaitori_prices_success(mock_get, scraper, mock_response):
    mock_get.return_value = mock_response
    prices = scraper.get_kaitori_prices()
    assert len(prices) > 0
    assert all(isinstance(price, PriceData) for price in prices)

@patch('requests.get')
def test_get_kaitori_prices_retry(mock_get, scraper):
    mock_get.side_effect = [
        Exception("Connection error"),
        MagicMock(text=MOCK_HTML, status_code=200)
    ]
    prices = scraper.get_kaitori_prices()
    assert len(prices) > 0
    assert all(isinstance(price, PriceData) for price in prices)

@patch('requests.get')
def test_get_official_prices_success(mock_get, scraper, mock_official_response):
    mock_get.return_value = mock_official_response
    prices = scraper.get_official_prices()
    assert len(prices) > 0
    assert all(isinstance(price, PriceData) for price in prices)

@patch('requests.get')
def test_get_official_prices_no_elements(mock_get, scraper):
    mock_get.return_value = MagicMock(text="<html><body></body></html>", status_code=200)
    prices = scraper.get_official_prices()
    assert len(prices) == 0

@patch('requests.get')
def test_get_official_prices_request_error(mock_get, scraper):
    mock_get.side_effect = Exception("Connection failed")
    with pytest.raises(ScraperError):
        scraper.get_official_prices()

@patch('requests.get')
def test_get_official_prices_invalid_html(mock_get, scraper):
    mock_get.return_value = MagicMock(text="<div>Invalid HTML</div>", status_code=200)
    prices = scraper.get_official_prices()
    assert len(prices) == 0

def test_scrape_url_performance_tracking(scraper):
    with patch('time.time') as mock_time:
        mock_time.side_effect = [0, 1]  # 1秒の実行時間をシミュレート
        result = scraper.scrape_url("https://example.com", source="test")
        assert scraper.performance_metrics["total_time"] == 1.0

def test_error_handling(scraper):
    with pytest.raises(ScraperError):
        scraper.scrape_url("invalid-url", source="test")

def test_retry_mechanism(scraper):
    with patch('requests.get') as mock_get:
        mock_get.side_effect = [
            Exception("Connection error"),
            MagicMock(text=MOCK_HTML, status_code=200)
        ]
        result = scraper.scrape_url("https://example.com", source="test")
        assert len(result) > 0

def test_cache_mechanism(scraper):
    url = "https://example.com"
    with patch('requests.get') as mock_get:
        mock_get.return_value = MagicMock(text=MOCK_HTML, status_code=200)
        # 最初のリクエスト
        scraper.scrape_url(url, source="test")
        # 2回目のリクエスト（キャッシュヒット）
        scraper.scrape_url(url, source="test")
        assert url in scraper.cache_manager.cache_hits

@patch('requests.get')
def test_concurrent_scraping(mock_get, scraper):
    mock_get.return_value = MagicMock(text=MOCK_HTML, status_code=200)
    urls = ["https://example1.com", "https://example2.com"]
    results = scraper.scrape_urls(urls, source="test")
    assert len(results) == len(urls)

def test_scrape_url_validation_error_handling(scraper):
    with patch('requests.get') as mock_get:
        mock_get.return_value = MagicMock(text="<div>Invalid HTML</div>", status_code=200)
        result = scraper.scrape_url("https://example.com", source="test")
        assert len(result) == 0

def test_scrape_url_cache_error_handling(scraper):
    with patch('requests.get') as mock_get:
        mock_get.side_effect = Exception("Cache error")
        with pytest.raises(ScraperError):
            scraper.scrape_url("https://example.com", source="test")

def test_scrape_url_critical_error_handling(scraper):
    with patch('requests.get') as mock_get:
        mock_get.side_effect = Exception("Critical error")
        with pytest.raises(ScraperError):
            scraper.scrape_url("https://example.com", source="test")

def test_error_severity_enum():
    assert ErrorSeverity.LOW.value == "LOW"
    assert ErrorSeverity.MEDIUM.value == "MEDIUM"
    assert ErrorSeverity.HIGH.value == "HIGH"

def test_scraper_error_initialization():
    error = ScraperError("Test error", ErrorSeverity.MEDIUM)
    assert error.message == "Test error"
    assert error.severity == ErrorSeverity.MEDIUM

def test_http_error_initialization():
    error = ScraperError("HTTP error", ErrorSeverity.HIGH)
    assert error.message == "HTTP error"
    assert error.severity == ErrorSeverity.HIGH

def test_parse_error_initialization():
    error = ScraperError("Parse error", ErrorSeverity.MEDIUM)
    assert error.message == "Parse error"
    assert error.severity == ErrorSeverity.MEDIUM

def test_validation_error_initialization():
    error = ScraperError("Validation error", ErrorSeverity.MEDIUM)
    assert error.message == "Validation error"
    assert error.severity == ErrorSeverity.MEDIUM

def test_cache_error_initialization():
    error = ScraperError("Cache error", ErrorSeverity.LOW)
    assert error.message == "Cache error"
    assert error.severity == ErrorSeverity.LOW

def test_error_handler_initialization():
    handler = ErrorHandler()
    assert handler is not None
    assert len(handler.errors) == 0

def test_error_handler_handle_error():
    handler = ErrorHandler()
    handler.handle_error("Test error 1", ErrorSeverity.LOW)
    handler.handle_error("Test error 2", ErrorSeverity.MEDIUM, {"html_snippet": "", "selector": ""})
    handler.handle_error("Test error 3", ErrorSeverity.HIGH)
    assert len(handler.errors) == 3

def test_error_handler_get_summary():
    handler = ErrorHandler()
    handler.handle_error("Test error 1", ErrorSeverity.LOW)
    handler.handle_error("Test error 2", ErrorSeverity.MEDIUM, {"html_snippet": "", "selector": ""})
    summary = handler.get_summary()
    assert "LOW" in summary
    assert "MEDIUM" in summary

def test_error_handler_should_continue():
    handler = ErrorHandler()
    handler.handle_error("Test error", ErrorSeverity.HIGH)
    handler.handle_error("Test error", ErrorSeverity.HIGH)
    handler.handle_error("Test error", ErrorSeverity.HIGH)
    assert not handler.should_continue()

def test_scraper_consecutive_high_severity_errors(scraper):
    with patch('requests.get') as mock_get:
        mock_get.return_value = MagicMock(text="<html><body></body></html>", status_code=200)
        for _ in range(3):
            scraper.scrape_url("https://example.com", source="test")
        assert not scraper.error_handler.should_continue()

def test_scraper_error_context(scraper):
    with patch('requests.get') as mock_get:
        mock_get.return_value = MagicMock(text="<html><body></body></html>", status_code=200)
        scraper.scrape_url("https://example.com", source="test")
        assert len(scraper.error_handler.errors) > 0
        error = scraper.error_handler.errors[0]
        assert "context" in error

def test_scraper_error_id_generation(scraper):
    with patch('requests.get') as mock_get:
        mock_get.return_value = MagicMock(text="<html><body></body></html>", status_code=200)
        scraper.scrape_url("https://example.com", source="test")
        assert len(scraper.error_handler.errors) > 0
        error = scraper.error_handler.errors[0]
        assert "error_id" in error

def test_scraper_error_timestamp(scraper):
    with patch('requests.get') as mock_get:
        mock_get.return_value = MagicMock(text="<html><body></body></html>", status_code=200)
        scraper.scrape_url("https://example.com", source="test")
        assert len(scraper.error_handler.errors) > 0
        error = scraper.error_handler.errors[0]
        assert "timestamp" in error

def test_scraper_performance_metrics(scraper):
    with patch('requests.get') as mock_get:
        mock_get.return_value = MagicMock(text="<html><body></body></html>", status_code=200)
        scraper.scrape_url("https://example.com", source="test")
        assert "total_time" in scraper.performance_metrics
        assert "request_count" in scraper.performance_metrics

@patch('requests.get')
def test_scraper_performance_metrics_multiple_requests(mock_get, scraper):
    mock_get.side_effect = [
        MagicMock(text=MOCK_HTML, status_code=200),
        MagicMock(text=MOCK_HTML, status_code=200)
    ]
    urls = ["https://example.com/1", "https://example.com/2"]
    scraper.scrape_urls(urls, source="test")
    assert scraper.performance_metrics["request_count"] == 2

@patch('requests.get')
def test_scraper_performance_metrics_timeout(mock_get, scraper):
    mock_get.side_effect = Exception("Timeout")
    with pytest.raises(ScraperError):
        scraper.scrape_url("https://example.com", source="test")
    assert "error_count" in scraper.performance_metrics 