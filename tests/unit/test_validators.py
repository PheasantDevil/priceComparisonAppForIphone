import pytest

from config import AppConfig, ScraperConfig
from config.manager import ConfigManager


class TestAppConfigValidation:
    def test_valid_app_config(self):
        """有効なアプリケーション設定のテスト"""
        config = AppConfig(
            DEBUG=True,
            SECRET_KEY="valid-secret-key-12345",
            LOG_LEVEL="DEBUG"
        )
        assert config.DEBUG is True
        assert config.SECRET_KEY == "valid-secret-key-12345"
        assert config.LOG_LEVEL == "DEBUG"

    def test_invalid_secret_key(self):
        """無効なシークレットキーのテスト"""
        with pytest.raises(ValueError, match="SECRET_KEY must be at least 16 characters"):
            AppConfig(
                DEBUG=True,
                SECRET_KEY="short",
                LOG_LEVEL="DEBUG"
            )

    def test_invalid_log_level(self):
        """無効なログレベルのテスト"""
        with pytest.raises(ValueError, match="LOG_LEVEL must be one of"):
            AppConfig(
                DEBUG=True,
                SECRET_KEY="valid-secret-key-12345",
                LOG_LEVEL="INVALID"
            )

class TestScraperConfigValidation:
    def test_valid_scraper_config(self):
        """有効なスクレイパー設定のテスト"""
        config = ScraperConfig(
            KAITORI_RUDEA_URLS=["https://example.com/kaitori"],
            APPLE_STORE_URL="https://example.com/apple",
            REQUEST_TIMEOUT=30,
            RETRY_COUNT=3,
            USER_AGENT="Test Agent"
        )
        assert len(config.KAITORI_RUDEA_URLS) == 1
        assert config.KAITORI_RUDEA_URLS[0] == "https://example.com/kaitori"

    def test_invalid_url_format(self):
        """無効なURL形式のテスト"""
        with pytest.raises(ValueError, match="Invalid URL format"):
            ScraperConfig(
                KAITORI_RUDEA_URLS=["invalid-url"],
                APPLE_STORE_URL="https://example.com",
                REQUEST_TIMEOUT=30,
                RETRY_COUNT=3,
                USER_AGENT="Test Agent"
            )

    def test_invalid_timeout(self):
        """無効なタイムアウト値のテスト"""
        with pytest.raises(ValueError, match="REQUEST_TIMEOUT must be a positive integer"):
            ScraperConfig(
                KAITORI_RUDEA_URLS=["https://example.com"],
                APPLE_STORE_URL="https://example.com",
                REQUEST_TIMEOUT=0,
                RETRY_COUNT=3,
                USER_AGENT="Test Agent"
            )

    def test_valid_scraper_config_with_multiple_urls(self):
        """複数のURLを持つ有効なスクレイパー設定のテスト"""
        config = ScraperConfig(
            KAITORI_RUDEA_URLS=["https://example.com/kaitori1", "https://example.com/kaitori2"],
            APPLE_STORE_URL="https://example.com/apple",
            REQUEST_TIMEOUT=30,
            RETRY_COUNT=3,
            USER_AGENT="Test Agent"
        )
        assert len(config.KAITORI_RUDEA_URLS) == 2
        assert config.KAITORI_RUDEA_URLS[0] == "https://example.com/kaitori1"
        assert config.KAITORI_RUDEA_URLS[1] == "https://example.com/kaitori2"

    def test_invalid_kaitori_rudea_urls(self):
        """無効なkaitori_rudea_urlsのテスト"""
        with pytest.raises(ValueError, match="Invalid URL format"):
            ScraperConfig(
                KAITORI_RUDEA_URLS=["https://example.com", "invalid-url"],
                APPLE_STORE_URL="https://example.com/apple",
                REQUEST_TIMEOUT=30,
                RETRY_COUNT=3,
                USER_AGENT="Test Agent"
            )

# 境界値テスト: REQUEST_TIMEOUT が 0 以下の場合はエラーを出す必要があります
def test_scraper_request_timeout_boundary():
    """REQUEST_TIMEOUT の境界値テスト"""
    with pytest.raises(ValueError, match="REQUEST_TIMEOUT must be a positive integer"):
        ScraperConfig(
            KAITORI_RUDEA_URLS=["https://example.com"],
            APPLE_STORE_URL="https://example.com",
            REQUEST_TIMEOUT=-1,  # 境界値（0 以下はエラー）
            RETRY_COUNT=1,
            USER_AGENT="Test Agent"
        )

# 無効な LOG_LEVEL を渡した場合のテスト
def test_app_log_level_invalid():
    """LOG_LEVEL が無効な場合のテスト"""
    with pytest.raises(ValueError, match="LOG_LEVEL must be one of"):
        # LOG_LEVEL に無効な値 "INVALID" を指定し、エラーハンドリングを確認
        AppConfig(
            DEBUG=True,
            SECRET_KEY="valid-secret-key-12345",
            LOG_LEVEL="INVALID"  # 無効な LOG_LEVEL
        )

# SECRET_KEY が設定されていない場合、デフォルト値が使用されるかのテスト
def test_config_environment_with_missing_secret_key(monkeypatch):
    """SECRET_KEY が存在しない場合のテスト"""
    # SECRET_KEY を削除して、デフォルト値が設定されるか確認
    monkeypatch.delenv("SECRET_KEY", raising=False)
    config = ConfigManager()
    # デフォルトのシークレットキーが使用されるか確認
    assert config.app.SECRET_KEY == "default-secret-key"  # デフォルト値として設定されている

# FLASK_ENV が production の場合に正しく設定されるか確認
def test_config_environment_with_different_env(monkeypatch):
    """異なる FLASK_ENV のテスト"""
    # FLASK_ENV を production に設定
    monkeypatch.setenv("FLASK_ENV", "production")
    config = ConfigManager()
    # 環境が production になっているか確認
    assert config.env == "production"

# 無効な SECRET_KEY を渡した場合のエラーハンドリングテスト
def test_invalid_secret_key_length(monkeypatch):
    """SECRET_KEY が無効な場合のテスト"""
    monkeypatch.setenv("SECRET_KEY", "short")
    with pytest.raises(ValueError, match="SECRET_KEY must be at least 16 characters"):
        config = ConfigManager()
        _ = config.app  # app プロパティにアクセスして初期化を強制

def test_config_manager_with_multiple_urls(monkeypatch, tmp_path):
    """複数のURLを持つConfigManagerのテスト"""
    config_content = """
    app:
      debug: true
      log_level: DEBUG
      secret_key: test-secret-key-16ch

    scraper:
      kaitori_rudea_urls:
        - https://test1.example.com/kaitori
        - https://test2.example.com/kaitori
      apple_store_url: https://test.example.com/apple
      request_timeout: 30
      retry_count: 3
      user_agent: "Test User Agent"
    """
    config_file = tmp_path / "config.testing.yaml"
    config_file.write_text(config_content)

    monkeypatch.setenv("FLASK_ENV", "testing")
    config = ConfigManager(config_dir=tmp_path)

    assert len(config.scraper.KAITORI_RUDEA_URLS) == 2
    assert "https://test1.example.com/kaitori" in config.scraper.KAITORI_RUDEA_URLS
    assert "https://test2.example.com/kaitori" in config.scraper.KAITORI_RUDEA_URLS

def test_scraper_config_with_iphone16_pro_url():
    """iPhone 16 Pro URLを含むスクレイパー設定のテスト"""
    config = ScraperConfig(
        KAITORI_RUDEA_URLS=[
            "https://kaitori-rudeya.com/category/detail/183",  # iPhone 16
            "https://kaitori-rudeya.com/category/detail/185",  # iPhone 16 Pro
            "https://kaitori-rudeya.com/category/detail/186"   # iPhone 16 Pro Max
        ],
        APPLE_STORE_URL="https://example.com/apple",
        REQUEST_TIMEOUT=30,
        RETRY_COUNT=3,
        USER_AGENT="Test Agent"
    )
    assert len(config.KAITORI_RUDEA_URLS) == 3
    assert "https://kaitori-rudeya.com/category/detail/185" in config.KAITORI_RUDEA_URLS

def test_config_manager_loads_iphone16_pro_url(mock_env_vars, tmp_path):
    """ConfigManagerがiPhone 16 Pro URLを正しく読み込むかテスト"""
    config_content = """
    app:
      debug: true
      log_level: DEBUG
      secret_key: test-secret-key-16ch

    scraper:
      kaitori_rudea_urls:
        - https://kaitori-rudeya.com/category/detail/183
        - https://kaitori-rudeya.com/category/detail/185
        - https://kaitori-rudeya.com/category/detail/186
      apple_store_url: https://example.com/apple
      request_timeout: 30
      retry_count: 3
      user_agent: "Test User Agent"
    """
    config_file = tmp_path / "config.testing.yaml"
    config_file.write_text(config_content)

    monkeypatch = mock_env_vars
    monkeypatch.setenv("FLASK_ENV", "testing")
    config = ConfigManager(config_dir=tmp_path)

    assert len(config.scraper.KAITORI_RUDEA_URLS) == 3
    assert "https://kaitori-rudeya.com/category/detail/185" in config.scraper.KAITORI_RUDEA_URLS
