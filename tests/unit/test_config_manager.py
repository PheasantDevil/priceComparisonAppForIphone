import os
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from src.lambda_functions.get_prices_lambda.config.manager import ConfigManager


@pytest.fixture
def mock_config_data():
    return """
    scraper:
      timeout: 30
      max_retries: 3
      cache_expiry: 3600
      user_agent: "Mozilla/5.0"
    
    dynamodb:
      table_name: "price_comparison"
      region: "ap-northeast-1"
    
    urls:
      kaitori_rudea:
        - "https://example.com/kaitori1"
        - "https://example.com/kaitori2"
      official:
        - "https://example.com/official1"
        - "https://example.com/official2"
    """

@pytest.fixture
def config_manager():
    return ConfigManager()

def test_config_manager_initialization():
    """ConfigManagerの初期化テスト"""
    manager = ConfigManager()
    assert manager.config is None
    assert manager.config_path is not None

def test_load_config_success(config_manager, mock_config_data):
    """設定ファイルの読み込み成功テスト"""
    with patch("builtins.open", mock_open(read_data=mock_config_data)):
        config_manager.load_config()
        assert config_manager.config is not None
        assert "scraper" in config_manager.config
        assert "dynamodb" in config_manager.config
        assert "urls" in config_manager.config

def test_load_config_file_not_found(config_manager):
    """設定ファイルが存在しない場合のテスト"""
    with pytest.raises(FileNotFoundError):
        config_manager.load_config()

def test_load_config_invalid_yaml(config_manager):
    """無効なYAML形式のテスト"""
    invalid_yaml = "invalid: yaml: content:"
    with patch("builtins.open", mock_open(read_data=invalid_yaml)):
        with pytest.raises(Exception):
            config_manager.load_config()

def test_get_scraper_config(config_manager, mock_config_data):
    """スクレイパー設定の取得テスト"""
    with patch("builtins.open", mock_open(read_data=mock_config_data)):
        config_manager.load_config()
        scraper_config = config_manager.get_scraper_config()
        assert scraper_config["timeout"] == 30
        assert scraper_config["max_retries"] == 3
        assert scraper_config["cache_expiry"] == 3600
        assert scraper_config["user_agent"] == "Mozilla/5.0"

def test_get_dynamodb_config(config_manager, mock_config_data):
    """DynamoDB設定の取得テスト"""
    with patch("builtins.open", mock_open(read_data=mock_config_data)):
        config_manager.load_config()
        dynamodb_config = config_manager.get_dynamodb_config()
        assert dynamodb_config["table_name"] == "price_comparison"
        assert dynamodb_config["region"] == "ap-northeast-1"

def test_get_urls_config(config_manager, mock_config_data):
    """URL設定の取得テスト"""
    with patch("builtins.open", mock_open(read_data=mock_config_data)):
        config_manager.load_config()
        urls_config = config_manager.get_urls_config()
        assert "kaitori_rudea" in urls_config
        assert "official" in urls_config
        assert len(urls_config["kaitori_rudea"]) == 2
        assert len(urls_config["official"]) == 2

def test_get_config_without_loading(config_manager):
    """設定を読み込まずに取得しようとした場合のテスト"""
    with pytest.raises(Exception):
        config_manager.get_scraper_config()

def test_custom_config_path():
    """カスタム設定ファイルパスのテスト"""
    custom_path = "/path/to/custom/config.yaml"
    manager = ConfigManager(config_path=custom_path)
    assert manager.config_path == custom_path 