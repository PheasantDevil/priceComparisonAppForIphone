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
    assert "http" in config.scraper.KAITORI_RUDEA_URL
    assert "http" in config.scraper.APPLE_STORE_URL

# ConfigManager の統合テスト: 設定ファイルと環境変数が正しく統合されるか確認
def test_config_integration_with_file_and_env(monkeypatch, test_config_file):
    """設定ファイルと環境変数の統合テスト"""
    # FLASK_ENV を testing に、SECRET_KEY を env-secret-key に設定
    monkeypatch.setenv("FLASK_ENV", "testing")
    monkeypatch.setenv("SECRET_KEY", "env-secret-key")
    config = ConfigManager(config_dir=test_config_file.parent)
    
    # 統合後の ConfigManager が正しく値を取得しているか確認
    assert config.app.SECRET_KEY == "env-secret-key"  # 環境変数が優先される
    assert config.app.DEBUG is True  # 設定ファイルから取得
    assert config.scraper.REQUEST_TIMEOUT == 30  # 設定ファイルから取得
