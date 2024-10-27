import pytest
from pathlib import Path

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
