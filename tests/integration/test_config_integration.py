from pathlib import Path

import pytest

from config import ConfigManager


def test_config_environment_integration(mock_env_vars, test_config_file):
    """設定ファイルと環境変数の統合テスト"""
    config = ConfigManager(config_dir=test_config_file.parent)
    
    # 環境変数からの値
    assert config.app.SECRET_KEY == mock_env_vars["SECRET_KEY"]
    
    # 設定ファイルからの値
    assert isinstance(config.app.DEBUG, bool)
    assert config.app.LOG_LEVEL in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

def test_scraper_config_integration(mock_env_vars, test_config_file):
    """スクレイパー設定の統合テスト"""
    config = ConfigManager(config_dir=test_config_file.parent)
    
    assert config.scraper.REQUEST_TIMEOUT > 0
    assert config.scraper.RETRY_COUNT >= 0
    assert all("http" in url for url in config.scraper.KAITORI_RUDEA_URLS)
    assert "http" in config.scraper.APPLE_STORE_URL

# ConfigManager の統合テスト: 設定ファイルと環境変数が正しく統合されるか確認
def test_config_integration_with_file_and_env(monkeypatch, test_config_file):
    """設定ファイルと環境変数の統合テスト"""
    monkeypatch.setenv("FLASK_ENV", "testing")
    monkeypatch.setenv("SECRET_KEY", "env-secret-key-16ch")  # 16文字以上に変更
    config = ConfigManager(config_dir=test_config_file.parent)
    
    # 統合後の ConfigManager が正しく値を取得しているか確認
    assert config.app.SECRET_KEY == "env-secret-key-16ch"  # 環境変数が優先される
    assert config.app.DEBUG is True  # 設定ファイルから取得
    assert config.scraper.REQUEST_TIMEOUT == 30  # 設定ファイルから取得

# 設定ファイルが存在しない場合のテスト
def test_config_file_not_found():
    """設定ファイルが見つからない場合のエラーハンドリング"""
    # 存在しないディレクトリを指定して ConfigManager を初期化
    with pytest.raises(FileNotFoundError, match="Configuration file not found"):
        ConfigManager(config_dir="non_existent_directory")

def test_iphone16_pro_url_integration(mock_env_vars, test_config_file):
    """iPhone 16 Pro URLの統合テスト"""
    config = ConfigManager(config_dir=test_config_file.parent)
    
    # 全てのiPhoneモデルのURLが含まれているか確認
    expected_urls = [
        "https://kaitori-rudeya.com/category/detail/183",  # iPhone 16
        "https://kaitori-rudeya.com/category/detail/185",  # iPhone 16 Pro
        "https://kaitori-rudeya.com/category/detail/186"   # iPhone 16 Pro Max
    ]
    
    # URLの数が正しいか確認
    assert len(config.scraper.KAITORI_RUDEA_URLS) == len(expected_urls)
    
    # 各URLが正しく含まれているか確認
    for url in expected_urls:
        assert url in config.scraper.KAITORI_RUDEA_URLS
        
    # URLの順序が正しいか確認
    assert config.scraper.KAITORI_RUDEA_URLS == expected_urls
