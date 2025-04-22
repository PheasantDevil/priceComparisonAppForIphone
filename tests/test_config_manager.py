import shutil
import sys
from pathlib import Path

import pytest

# プロジェクトのルートディレクトリをPYTHONPATHに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest

from config import AppConfig, ConfigManager, ScraperConfig


@pytest.fixture(scope="function")
def test_config_file(tmp_path):
    config_content = """
app:
  debug: true
  log_level: "DEBUG"

scraper:
  kaitori_rudea_urls:
    - "https://kaitori-rudeya.com/category/detail/183"  # iPhone 16
    - "https://kaitori-rudeya.com/category/detail/185"  # iPhone 16 Pro
    - "https://kaitori-rudeya.com/category/detail/186"  # iPhone 16 Pro Max
    - "https://kaitori-rudeya.com/category/detail/205"  # iPhone 16 e
  apple_store_url: "https://example.com/apple"
  request_timeout: 30
  retry_count: 3
  user_agent: "Test User Agent"
"""
    config_file = tmp_path / "config.testing.yaml"
    config_file.write_text(config_content)
    
    # ConfigManagerが参照するディレクトリにファイルをコピー
    dest_dir = Path(__file__).parent.parent / "config"
    dest_file = dest_dir / "config.testing.yaml"
    shutil.copy(str(config_file), str(dest_file))
    
    yield dest_file
    
    # テスト後にファイルを削除
    dest_file.unlink()

def test_config_manager_initialization(mock_env_vars, test_config_file):
    """ConfigManagerの初期化テスト"""
    config = ConfigManager()
    assert config.env == "testing"
    assert isinstance(config.app, AppConfig)
    assert isinstance(config.scraper, ScraperConfig)

def test_app_config_validation():
    """AppConfigのバリデーションテスト"""
    with pytest.raises(ValueError, match="SECRET_KEY must be at least 16 characters"):
        AppConfig(
            DEBUG=True,
            SECRET_KEY="short",
            LOG_LEVEL="DEBUG"
        )
    
    with pytest.raises(ValueError, match="LOG_LEVEL must be one of"):
        AppConfig(
            DEBUG=True,
            SECRET_KEY="valid-secret-key-12345",
            LOG_LEVEL="INVALID"
        )

def test_scraper_config_validation():
    """ScraperConfigのバリデーションテスト"""
    with pytest.raises(ValueError, match="Invalid URL format"):
        ScraperConfig(
            KAITORI_RUDEA_URLS=["invalid-url"],
            APPLE_STORE_URL="https://example.com",
            REQUEST_TIMEOUT=30,
            RETRY_COUNT=3,
            USER_AGENT="Test Agent"
        )
    
    with pytest.raises(ValueError, match="REQUEST_TIMEOUT must be a positive integer"):
        ScraperConfig(
            KAITORI_RUDEA_URLS=["https://example.com"],
            APPLE_STORE_URL="https://example.com",
            REQUEST_TIMEOUT=0,
            RETRY_COUNT=3,
            USER_AGENT="Test Agent"
        )

def test_scraper_config_multiple_urls(mock_env_vars, test_config_file):
    """複数のkaitori_rudea_urlsを持つScraperConfigのテスト"""
    config = ConfigManager()
    assert isinstance(config.scraper.KAITORI_RUDEA_URLS, list)
    assert len(config.scraper.KAITORI_RUDEA_URLS) == 4
    assert "https://kaitori-rudeya.com/category/detail/183" in config.scraper.KAITORI_RUDEA_URLS
    assert "https://kaitori-rudeya.com/category/detail/185" in config.scraper.KAITORI_RUDEA_URLS
    assert "https://kaitori-rudeya.com/category/detail/186" in config.scraper.KAITORI_RUDEA_URLS
    assert "https://kaitori-rudeya.com/category/detail/205" in config.scraper.KAITORI_RUDEA_URLS
