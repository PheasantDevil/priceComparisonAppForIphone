#!/usr/bin/env python3
"""
スクレイピング機能のテスト
"""

import json
import os
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from scripts.price_scraping.scrape_prices import PriceScraper

# テスト用の設定
TEST_CONFIG = {
    'scraper': {
        'kaitori_rudea_urls': [
            'https://test.example.com/iphone16',
            'https://test.example.com/iphone16pro'
        ]
    }
}

# テスト用のHTML
TEST_HTML = """
<div class="tr">
    <div class="ttl">
        <h2>iPhone 16 Pro 128GB 黒</h2>
    </div>
    <div class="td td2">
        <div class="td2wrap">123,456円</div>
    </div>
</div>
<div class="tr">
    <div class="ttl">
        <h2>iPhone 16 Pro 256GB 白</h2>
    </div>
    <div class="td td2">
        <div class="td2wrap">234,567円</div>
    </div>
</div>
"""

@pytest.fixture
def mock_config():
    """設定ファイルのモック"""
    with patch('scripts.price_scraping.scrape_prices.Path') as mock_path:
        # 実際のファイルパスを使用
        config_path = Path(__file__).parent.parent.parent / 'config' / 'config.testing.yaml'
        mock_path.return_value = config_path
        yield mock_path

@pytest.fixture
def mock_dynamodb():
    """DynamoDBのモック"""
    with patch('boto3.resource') as mock_resource:
        mock_table = MagicMock()
        mock_resource.return_value.Table.return_value = mock_table
        yield mock_table

@pytest.fixture
def mock_playwright():
    """Playwrightのモック"""
    with patch('playwright.async_api.async_playwright') as mock_playwright:
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_playwright.return_value.__aenter__.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        mock_page.query_selector_all.return_value = [
            AsyncMock(
                query_selector=AsyncMock(
                    side_effect=lambda selector: AsyncMock(
                        inner_text=AsyncMock(
                            return_value="iPhone 16 Pro 128GB 黒" if selector == ".ttl h2" else "123,456円"
                        )
                    ) if selector == ".ttl h2" or selector == ".td.td2 .td2wrap" else None
                )
            ),
            AsyncMock(
                query_selector=AsyncMock(
                    side_effect=lambda selector: AsyncMock(
                        inner_text=AsyncMock(
                            return_value="iPhone 16 Pro 256GB 白" if selector == ".ttl h2" else "234,567円"
                        )
                    ) if selector == ".ttl h2" or selector == ".td.td2 .td2wrap" else None
                )
            )
        ]
        yield mock_playwright

@pytest.mark.asyncio
async def test_scrape_url(mock_config, mock_playwright):
    """URLからのスクレイピングテスト"""
    scraper = PriceScraper()
    result = await scraper.scrape_url('https://test.example.com/iphone16pro')
    
    assert result['series'] == 'iPhone 16 Pro'
    assert result['capacity'] == '128GB'
    assert result['colors']['黒']['price_value'] == 123456
    assert result['kaitori_price_min'] == 123456
    assert result['kaitori_price_max'] == 234567

@pytest.mark.asyncio
async def test_scrape_all_prices(mock_config, mock_playwright):
    """全URLからのスクレイピングテスト"""
    scraper = PriceScraper()
    results = await scraper.scrape_all_prices()
    
    assert len(results) == 2
    assert all(not isinstance(result, Exception) for result in results)
    assert all('series' in result for result in results)
    assert all('capacity' in result for result in results)
    assert all('colors' in result for result in results)

def test_save_to_dynamodb(mock_config, mock_dynamodb):
    """DynamoDBへの保存テスト"""
    scraper = PriceScraper()
    test_data = {
        'id': 'iPhone_16_Pro_128GB',
        'series': 'iPhone 16 Pro',
        'capacity': '128GB',
        'colors': {
            '黒': {
                'price_text': '123,456円',
                'price_value': 123456
            }
        },
        'kaitori_price_min': 123456,
        'kaitori_price_max': 123456
    }
    
    scraper.save_to_dynamodb(test_data)
    
    # kaitori_pricesテーブルへの保存を確認
    mock_dynamodb.put_item.assert_called()
    call_args = mock_dynamodb.put_item.call_args[1]['Item']
    assert call_args['id'] == test_data['id']
    assert call_args['series'] == test_data['series']
    assert call_args['capacity'] == test_data['capacity']
    assert call_args['colors'] == test_data['colors']

def test_delete_old_data(mock_config, mock_dynamodb):
    """古いデータの削除テスト"""
    scraper = PriceScraper()
    mock_dynamodb.scan.return_value = {
        'Items': [
            {
                'model': 'iPhone_16_Pro_128GB',
                'timestamp': int((datetime.now().timestamp() - 15 * 24 * 60 * 60))  # 15日前
            }
        ]
    }
    
    scraper.delete_old_data()
    
    # 古いデータの削除を確認
    mock_dynamodb.batch_writer.assert_called_once()
    mock_dynamodb.scan.assert_called_once()

def test_price_text_to_int():
    """価格テキストの変換テスト"""
    scraper = PriceScraper()
    
    assert scraper._price_text_to_int('123,456円') == 123456
    assert scraper._price_text_to_int('1,234,567円') == 1234567
    assert scraper._price_text_to_int('0円') == 0
    assert scraper._price_text_to_int('') == 0
    assert scraper._price_text_to_int('invalid') == 0 