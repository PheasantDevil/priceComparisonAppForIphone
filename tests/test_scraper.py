import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.lambda_functions.get_prices_lambda.scraper import (CacheError,
                                                            HTTPError,
                                                            ParseError,
                                                            Scraper,
                                                            ScraperError,
                                                            ValidationError)


def test_scraper_initialization(mock_config):
    """Test scraper initialization with default configuration."""
    scraper = Scraper(mock_config)
    assert scraper.config == mock_config['scraper']
    assert scraper.selectors == mock_config['scraper']['selectors']
    assert scraper.headers == mock_config['scraper']['headers']
    assert scraper.max_retries == mock_config['scraper']['max_retries']
    assert scraper.timeout == mock_config['scraper']['timeout']
    assert scraper.cache_duration == mock_config['scraper']['cache_duration']

def test_scraper_initialization_with_config_file(test_config_file):
    """Test scraper initialization with configuration file."""
    scraper = Scraper(config_file=test_config_file)
    assert scraper.config_file == test_config_file
    assert scraper.selectors is not None
    assert scraper.headers is not None
    assert scraper.max_retries is not None
    assert scraper.timeout is not None
    assert scraper.cache_duration is not None

@patch('requests.get')
def test_scrape_url(mock_get, mock_response, mock_config, mock_cache_dir):
    """Test scraping a URL and extracting price data."""
    mock_get.return_value = mock_response
    scraper = Scraper(mock_config)
    scraper.cache_dir = mock_cache_dir

    url = "https://example.com"
    results = scraper.scrape_url(url)

    assert len(results) == 2
    assert results[0]['model'] == "iPhone 15 Pro 256GB"
    assert results[0]['price'] == 150000
    assert results[0]['condition'] == "新品"
    assert results[1]['model'] == "iPhone 15 Pro Max 512GB"
    assert results[1]['price'] == 180000
    assert results[1]['condition'] == "中古"

@patch('requests.get')
def test_scrape_url_cache(mock_get, mock_response, mock_config, mock_cache_dir):
    """Test caching functionality of the scraper."""
    mock_get.return_value = mock_response
    scraper = Scraper(mock_config)
    scraper.cache_dir = mock_cache_dir

    url = "https://example.com"
    
    # First request - should make HTTP call
    results1 = scraper.scrape_url(url)
    assert mock_get.call_count == 1
    
    # Second request - should use cache
    results2 = scraper.scrape_url(url)
    assert mock_get.call_count == 1  # No additional HTTP calls
    assert results1 == results2

@patch('requests.get')
def test_scrape_urls_parallel(mock_get, mock_response, mock_config):
    """Test parallel URL scraping."""
    mock_get.return_value = mock_response
    scraper = Scraper(config=mock_config)
    urls = ['https://example.com/1', 'https://example.com/2']
    results = scraper.scrape_urls(urls)
    assert len(results) == 2
    assert all(len(result) == 2 for result in results.values())

@patch('requests.get')
def test_scrape_url_http_error(mock_get, mock_config):
    """Test handling of HTTP errors during scraping."""
    mock_get.side_effect = HTTPError("Failed to fetch URL")
    scraper = Scraper(mock_config)

    with pytest.raises(HTTPError):
        scraper.scrape_url("https://example.com")

@patch('requests.get')
def test_scrape_url_parse_error(mock_get, mock_config):
    """Test handling of parsing errors during scraping."""
    mock_response = MagicMock()
    mock_response.text = "<invalid>html"
    mock_get.return_value = mock_response
    scraper = Scraper(mock_config)

    with pytest.raises(ParseError):
        scraper.scrape_url("https://example.com")

@patch('requests.get')
def test_scrape_url_validation_error(mock_get, mock_config):
    """Test handling of validation errors during scraping."""
    mock_response = MagicMock()
    mock_response.text = """
    <div class="price-item">
        <div class="model">Invalid Model</div>
        <div class="price">invalid_price</div>
        <div class="condition">新品</div>
    </div>
    """
    mock_get.return_value = mock_response
    scraper = Scraper(mock_config)

    with pytest.raises(ValidationError):
        scraper.scrape_url("https://example.com")

def test_scrape_url_cache_error(mock_config, mock_cache_dir):
    """Test handling of cache errors during scraping."""
    scraper = Scraper(mock_config)
    scraper.cache_dir = mock_cache_dir / "nonexistent"  # Invalid cache directory

    with pytest.raises(CacheError):
        scraper.scrape_url("https://example.com")

def test_performance_metrics(mock_config):
    """Test performance metrics collection."""
    scraper = Scraper(mock_config)
    metrics = scraper.get_performance_metrics()

    assert isinstance(metrics, dict)
    assert 'total_requests' in metrics
    assert 'cache_hits' in metrics
    assert 'cache_misses' in metrics
    assert 'average_response_time' in metrics
    assert all(isinstance(v, (int, float)) for v in metrics.values())

def test_retry_logic(mock_config):
    """Test retry logic for failed requests."""
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = [
        HTTPError('500 Internal Server Error'),
        HTTPError('500 Internal Server Error'),
        mock_response
    ]
    with patch('requests.get', return_value=mock_response):
        scraper = Scraper(config=mock_config)
        with pytest.raises(HTTPError):
            scraper.scrape_url('https://example.com')
        assert mock_response.raise_for_status.call_count == 3 