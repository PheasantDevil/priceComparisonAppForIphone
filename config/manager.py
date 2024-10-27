import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional, Union
from urllib.parse import urlparse

import yaml
from dotenv import load_dotenv


@dataclass(frozen=True)
class ScraperConfig:
    """スクレイピング関連の設定を管理するデータクラス"""
    KAITORI_RUDEA_URL: list  # str から list に変更
    APPLE_STORE_URL: str
    REQUEST_TIMEOUT: int
    RETRY_COUNT: int
    USER_AGENT: str

    # ScraperConfig 型検証を __post_init__ メソッド内で実装
    def __post_init__(self):
        self._validate_urls()
        self._validate_timeout()
        self._validate_retry_count()
        # 型チェック
        if not isinstance(self.KAITORI_RUDEA_URL, list):  # list のチェックに変更
            raise TypeError("KAITORI_RUDEA_URL must be a list of strings")
        if not isinstance(self.APPLE_STORE_URL, str):
            raise TypeError("APPLE_STORE_URL must be a string")
        if not isinstance(self.REQUEST_TIMEOUT, int):
            raise TypeError("REQUEST_TIMEOUT must be an integer")
        if not isinstance(self.RETRY_COUNT, int):
            raise TypeError("RETRY_COUNT must be an integer")
        if not isinstance(self.USER_AGENT, str):
            raise TypeError("USER_AGENT must be a string")

    def _validate_urls(self) -> None:
        """URLの形式を検証"""
        for url in self.KAITORI_RUDEA_URL + [self.APPLE_STORE_URL]:  # リストの各URLをチェック
            parsed = urlparse(url)
            if not all([parsed.scheme, parsed.netloc]):
                raise ValueError(f"Invalid URL format: {url}")

    def _validate_timeout(self) -> None:
        """タイムアウト値の検証"""
        if not isinstance(self.REQUEST_TIMEOUT, int) or self.REQUEST_TIMEOUT <= 0:
            raise ValueError(f"REQUEST_TIMEOUT must be a positive integer, got {self.REQUEST_TIMEOUT}")

    def _validate_retry_count(self) -> None:
        """リトライ回数の検証"""
        if not isinstance(self.RETRY_COUNT, int) or self.RETRY_COUNT < 0:
            raise ValueError(f"RETRY_COUNT must be a non-negative integer, got {self.RETRY_COUNT}")

@dataclass(frozen=True)
class AppConfig:
    """アプリケーション全体の設定を管理するデータクラス"""
    DEBUG: bool
    SECRET_KEY: str
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    # AppConfig 型検証を __post_init__ メソッド内で実装
    def __post_init__(self):
        self._validate_secret_key()
        self._validate_log_level()
        # 型チェック
        if not isinstance(self.DEBUG, bool):
            raise TypeError("DEBUG must be a boolean")
        if not isinstance(self.SECRET_KEY, str):
            raise TypeError("SECRET_KEY must be a string")
        if not isinstance(self.LOG_LEVEL, str):
            raise TypeError("LOG_LEVEL must be a string")

    def _validate_secret_key(self) -> None:
        """シークレットキーの検証"""
        if not self.SECRET_KEY or len(self.SECRET_KEY) < 16:
            raise ValueError("SECRET_KEY must be at least 16 characters long")

    def _validate_log_level(self) -> None:
        """ログレベルの検証"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.LOG_LEVEL not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")

class ConfigManager:
    """設定を一元管理するクラス"""
    def __init__(self, config_dir=None):
        self._config: Optional[dict] = None
        self._scraper_config: Optional[ScraperConfig] = None
        self._app_config: Optional[AppConfig] = None
        
        self.load_environment()
        self.load_config_file(config_dir)

    def load_environment(self) -> None:
        """環境変数を読み込む"""
        load_dotenv()
        self.env: str = os.getenv('FLASK_ENV', 'development')
        
    def load_config_file(self, config_dir=None) -> None:
        """設定ファイルを読み込む"""
        if config_dir is None:
            config_dir = Path(__file__).parent
        else:
            config_dir = Path(config_dir)
        
        config_file = config_dir / f'config.{self.env}.yaml'
        
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
            
        with open(config_file, 'r') as f:
            self._config = yaml.safe_load(f)

    @property
    def scraper(self) -> ScraperConfig:
        """スクレイピング設定を取得"""
        if self._scraper_config is None:
            self._scraper_config = ScraperConfig(
                KAITORI_RUDEA_URL=self._config['scraper']['kaitori_rudea_urls'],  # 複数形に変更
                APPLE_STORE_URL=self._config['scraper']['apple_store_url'],
                REQUEST_TIMEOUT=self._config['scraper']['request_timeout'],
                RETRY_COUNT=self._config['scraper']['retry_count'],
                USER_AGENT=self._config['scraper']['user_agent']
            )
        return self._scraper_config

    @property
    def app(self) -> AppConfig:
        """アプリケーション設定を取得"""
        if self._app_config is None:
            self._app_config = AppConfig(
                DEBUG=self._config['app']['debug'],
                SECRET_KEY=os.getenv('SECRET_KEY', 'default-secret-key'),
                LOG_LEVEL=self._config['app']['log_level']
            )
        return self._app_config

# シングルトンインスタンスを作成
config = ConfigManager()
