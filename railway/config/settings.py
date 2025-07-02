"""
Railway設定管理
"""
import os
from dataclasses import dataclass
from typing import List


@dataclass
class RailwayConfig:
    """Railway設定"""
    project_id: str
    service_id: str = ""
    environment: str = "production"


@dataclass
class SlackConfig:
    """Slack設定"""
    webhook_url: str
    channel: str = "#alerts"
    username: str = "Railway Log Monitor"
    icon_emoji: str = ":steam_locomotive:"


@dataclass
class LogMonitorConfig:
    """ログ監視設定"""
    interval: int = 60
    max_logs_per_batch: int = 100
    important_keywords: List[str] = None
    log_levels: List[str] = None
    
    def __post_init__(self):
        if self.important_keywords is None:
            self.important_keywords = ["error", "failed", "timeout", "exception", "critical"]
        if self.log_levels is None:
            self.log_levels = ["ERROR", "WARN", "CRITICAL"]


# 設定インスタンス
railway_config = RailwayConfig(
    project_id=os.getenv("RAILWAY_PROJECT_ID", ""),
    service_id=os.getenv("RAILWAY_SERVICE_ID", ""),
    environment=os.getenv("RAILWAY_ENVIRONMENT", "production")
)

slack_config = SlackConfig(
    webhook_url=os.getenv("SLACK_WEBHOOK_URL", ""),
    channel=os.getenv("SLACK_CHANNEL", "#alerts"),
    username=os.getenv("SLACK_USERNAME", "Railway Log Monitor"),
    icon_emoji=os.getenv("SLACK_ICON_EMOJI", ":steam_locomotive:")
)

log_monitor_config = LogMonitorConfig(
    interval=int(os.getenv("LOG_MONITOR_INTERVAL", "60")),
    max_logs_per_batch=int(os.getenv("LOG_MONITOR_MAX_LOGS", "100")),
    important_keywords=os.getenv("LOG_MONITOR_KEYWORDS", "error,failed,timeout,exception,critical").split(","),
    log_levels=os.getenv("LOG_MONITOR_LEVELS", "ERROR,WARN,CRITICAL").split(",")
)


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