import pytest

from config import AppConfig, ScraperConfig


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
            KAITORI_RUDEA_URL="https://example.com/kaitori",
            APPLE_STORE_URL="https://example.com/apple",
            REQUEST_TIMEOUT=30,
            RETRY_COUNT=3,
            USER_AGENT="Test Agent"
        )
        assert config.REQUEST_TIMEOUT == 30
        assert config.RETRY_COUNT == 3

    def test_invalid_url_format(self):
        """無効なURL形式のテスト"""
        with pytest.raises(ValueError, match="Invalid URL format"):
            ScraperConfig(
                KAITORI_RUDEA_URL="invalid-url",
                APPLE_STORE_URL="https://example.com",
                REQUEST_TIMEOUT=30,
                RETRY_COUNT=3,
                USER_AGENT="Test Agent"
            )

    def test_invalid_timeout(self):
        """無効なタイムアウト値のテスト"""
        with pytest.raises(ValueError, match="REQUEST_TIMEOUT must be a positive integer"):
            ScraperConfig(
                KAITORI_RUDEA_URL="https://example.com",
                APPLE_STORE_URL="https://example.com",
                REQUEST_TIMEOUT=0,
                RETRY_COUNT=3,
                USER_AGENT="Test Agent"
            )

# 境界値テスト: REQUEST_TIMEOUT が 0 以下の場合はエラーを出す必要があります
def test_scraper_request_timeout_boundary():
    """REQUEST_TIMEOUT の境界値テスト"""
    with pytest.raises(ValueError, match="REQUEST_TIMEOUT must be a positive integer"):
        # REQUEST_TIMEOUT の値に -1 を指定し、エラーハンドリングを確認
        ScraperConfig(
            KAITORI_RUDEA_URL="https://example.com",
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
