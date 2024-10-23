import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv


@dataclass
class ScraperConfig:
    """スクレイピング関連の設定を管理するデータクラス"""
    KAITORI_RUDEA_URL: str
    APPLE_STORE_URL: str
    REQUEST_TIMEOUT: int
    RETRY_COUNT: int

@dataclass
class AppConfig:
    """アプリケーション全体の設定を管理するデータクラス"""
    DEBUG: bool
    SECRET_KEY: str
    LOG_LEVEL: str

class ConfigManager:
    """設定を一元管理するクラス"""
    def __init__(self):
        self.load_environment()
        self.load_config_file()
        
    def load_environment(self):
        """環境変数を読み込む"""
        load_dotenv()
        self.env = os.getenv('FLASK_ENV', 'development')
        
    def load_config_file(self):
        """設定ファイルを読み込む"""
        config_dir = Path(__file__).parent
        config_file = config_dir / f'config.{self.env}.yaml'
        
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
            
        with open(config_file, 'r') as f:
            self._config = yaml.safe_load(f)
            
    @property
    def scraper(self) -> ScraperConfig:
        """スクレイピング設定を取得"""
        return ScraperConfig(
            KAITORI_RUDEA_URL=self._config['scraper']['kaitori_rudea_url'],
            APPLE_STORE_URL=self._config['scraper']['apple_store_url'],
            REQUEST_TIMEOUT=self._config['scraper']['request_timeout'],
            RETRY_COUNT=self._config['scraper']['retry_count']
        )
        
    @property
    def app(self) -> AppConfig:
        """アプリケーション設定を取得"""
        return AppConfig(
            DEBUG=self._config['app']['debug'],
            SECRET_KEY=os.getenv('SECRET_KEY', 'default-secret-key'),
            LOG_LEVEL=self._config['app']['log_level']
        )

# シングルトンインスタンスを作成
config = ConfigManager()