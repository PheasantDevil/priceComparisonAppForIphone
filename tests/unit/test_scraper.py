import os
import sys
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

# プロジェクトのルートディレクトリをPythonパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.lambda_functions.get_prices_lambda.scraper import (
    HTTPError, ParseError, PriceData, ScraperError, get_kaitori_prices,
    get_official_prices)


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