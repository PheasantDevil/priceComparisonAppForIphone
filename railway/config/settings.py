"""
Railway関連の設定管理
"""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class RailwayConfig:
    """Railway設定クラス"""
    project_id: str
    service_id: Optional[str] = None
    environment: str = "production"
    
    @classmethod
    def from_env(cls) -> 'RailwayConfig':
        """環境変数から設定を読み込み"""
        return cls(
            project_id=os.getenv('RAILWAY_PROJECT_ID', ''),
            service_id=os.getenv('RAILWAY_SERVICE_ID'),
            environment=os.getenv('RAILWAY_ENVIRONMENT', 'production')
        )


@dataclass
class SlackConfig:
    """Slack通知設定クラス"""
    webhook_url: str
    channel: str = "#general"
    username: str = "Railway Log Monitor"
    icon_emoji: str = ":steam_locomotive:"
    
    @classmethod
    def from_env(cls) -> 'SlackConfig':
        """環境変数から設定を読み込み"""
        return cls(
            webhook_url=os.getenv('SLACK_WEBHOOK_URL', ''),
            channel=os.getenv('SLACK_CHANNEL', '#general'),
            username=os.getenv('SLACK_USERNAME', 'Railway Log Monitor'),
            icon_emoji=os.getenv('SLACK_ICON_EMOJI', ':steam_locomotive:')
        )


@dataclass
class LogMonitorConfig:
    """ログ監視設定クラス"""
    interval: int = 60  # 監視間隔（秒）
    max_logs_per_batch: int = 100  # 一度に取得する最大ログ数
    important_keywords: list = None
    log_levels: list = None
    
    def __post_init__(self):
        if self.important_keywords is None:
            self.important_keywords = [
                'error', 'exception', 'failed', 'critical',
                'deploy', 'restart', 'health', 'timeout',
                'price', 'scrape', 'update', 'database',
                'connection', 'memory', 'cpu', 'disk'
            ]
        
        if self.log_levels is None:
            self.log_levels = ['ERROR', 'WARN', 'CRITICAL']
    
    @classmethod
    def from_env(cls) -> 'LogMonitorConfig':
        """環境変数から設定を読み込み"""
        return cls(
            interval=int(os.getenv('LOG_MONITOR_INTERVAL', '60')) if os.getenv('LOG_MONITOR_INTERVAL', '60').isdigit() else 60,
            max_logs_per_batch=int(os.getenv('LOG_MONITOR_MAX_LOGS', '100')) if os.getenv('LOG_MONITOR_MAX_LOGS', '100').isdigit() else 100,
            important_keywords=[k.strip() for k in os.getenv('LOG_MONITOR_KEYWORDS', '').split(',') if k.strip()] if os.getenv('LOG_MONITOR_KEYWORDS') else None,
            log_levels=[l.strip() for l in os.getenv('LOG_MONITOR_LEVELS', '').split(',') if l.strip()] if os.getenv('LOG_MONITOR_LEVELS') else None
        )


# グローバル設定インスタンス
railway_config = RailwayConfig.from_env()
slack_config = SlackConfig.from_env()
log_monitor_config = LogMonitorConfig.from_env()


def validate_configs() -> bool:
    """設定の妥当性を検証"""
    errors = []
    
    if not railway_config.project_id:
        errors.append("RAILWAY_PROJECT_ID is required")
    
    if not slack_config.webhook_url:
        errors.append("SLACK_WEBHOOK_URL is required")
    
    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    return True 