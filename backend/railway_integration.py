"""
既存バックエンドアプリケーションからのRailwayユーティリティ統合例
"""

import logging
import os
import sys
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from railway import RailwayClient, SlackNotifier, validate_configs
    RAILWAY_AVAILABLE = True
except ImportError:
    RAILWAY_AVAILABLE = False
    logging.warning("Railway utilities not available")


class RailwayIntegration:
    """Railway統合クラス"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.railway_client = None
        self.slack_notifier = None
        
        if RAILWAY_AVAILABLE and validate_configs():
            try:
                self.railway_client = RailwayClient()
                self.slack_notifier = SlackNotifier()
                self.logger.info("Railway integration initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize Railway integration: {e}")
    
    def notify_deployment(self, environment: str = "production"):
        """デプロイメント完了を通知"""
        if not self.slack_notifier:
            return False
        
        try:
            success = self.slack_notifier.send_message(
                f"🚀 Application deployed to {environment}!",
                "INFO",
                attachments=[{
                    "color": "#36a64f",
                    "title": "Deployment Status",
                    "text": f"Successfully deployed to {environment}",
                    "fields": [
                        {
                            "title": "Environment",
                            "value": environment,
                            "short": True
                        },
                        {
                            "title": "Timestamp",
                            "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
                            "short": True
                        }
                    ]
                }]
            )
            
            if success:
                self.logger.info(f"Deployment notification sent for {environment}")
            else:
                self.logger.warning(f"Failed to send deployment notification for {environment}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending deployment notification: {e}")
            return False
    
    def notify_error(self, error: Exception, context: str = "Application"):
        """エラーを通知"""
        if not self.slack_notifier:
            return False
        
        try:
            error_message = f"❌ {context} Error: {str(error)}"
            
            success = self.slack_notifier.send_message(
                error_message,
                "ERROR",
                attachments=[{
                    "color": "#ff0000",
                    "title": "Error Details",
                    "text": f"**Context:** {context}\n**Error:** {str(error)}\n**Type:** {type(error).__name__}",
                    "fields": [
                        {
                            "title": "Timestamp",
                            "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
                            "short": True
                        }
                    ]
                }]
            )
            
            if success:
                self.logger.info(f"Error notification sent for {context}")
            else:
                self.logger.warning(f"Failed to send error notification for {context}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending error notification: {e}")
            return False
    
    def notify_price_update(self, series: str, count: int):
        """価格更新を通知"""
        if not self.slack_notifier:
            return False
        
        try:
            success = self.slack_notifier.send_message(
                f"💰 Price update completed for {series}",
                "INFO",
                attachments=[{
                    "color": "#36a64f",
                    "title": "Price Update Status",
                    "text": f"Successfully updated prices for {series}",
                    "fields": [
                        {
                            "title": "Series",
                            "value": series,
                            "short": True
                        },
                        {
                            "title": "Records Updated",
                            "value": str(count),
                            "short": True
                        },
                        {
                            "title": "Timestamp",
                            "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
                            "short": False
                        }
                    ]
                }]
            )
            
            if success:
                self.logger.info(f"Price update notification sent for {series}")
            else:
                self.logger.warning(f"Failed to send price update notification for {series}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending price update notification: {e}")
            return False
    
    def send_health_check(self):
        """ヘルスチェックを実行して通知"""
        if not self.slack_notifier or not self.railway_client:
            return False
        
        try:
            # プロジェクト情報を取得
            project_info = self.railway_client.get_project_info()
            
            if project_info:
                details = {
                    'project': project_info.get('name', 'Unknown'),
                    'services': len(project_info.get('services', [])),
                    'environment': 'production'
                }
                
                success = self.slack_notifier.send_health_check('healthy', details)
                
                if success:
                    self.logger.info("Health check notification sent")
                else:
                    self.logger.warning("Failed to send health check notification")
                
                return success
            else:
                self.logger.warning("Failed to get project info for health check")
                return False
                
        except Exception as e:
            self.logger.error(f"Error in health check: {e}")
            return False
    
    def get_recent_logs(self, limit: int = 10):
        """最近のログを取得"""
        if not self.railway_client:
            return []
        
        try:
            logs = self.railway_client.get_logs(limit=limit)
            self.logger.info(f"Retrieved {len(logs)} recent logs")
            return logs
        except Exception as e:
            self.logger.error(f"Error getting recent logs: {e}")
            return []


# グローバルインスタンス
railway_integration = RailwayIntegration()


def notify_deployment(environment: str = "production"):
    """デプロイメント完了を通知（グローバル関数）"""
    return railway_integration.notify_deployment(environment)


def notify_error(error: Exception, context: str = "Application"):
    """エラーを通知（グローバル関数）"""
    return railway_integration.notify_error(error, context)


def notify_price_update(series: str, count: int):
    """価格更新を通知（グローバル関数）"""
    return railway_integration.notify_price_update(series, count)


def send_health_check():
    """ヘルスチェックを実行（グローバル関数）"""
    return railway_integration.send_health_check() 