"""
Slack通知ユーティリティ
"""
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

import requests

from ..config.settings import slack_config


class SlackNotifier:
    """Slack通知クラス"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {
            'webhook_url': slack_config.webhook_url,
            'channel': slack_config.channel,
            'username': slack_config.username,
            'icon_emoji': slack_config.icon_emoji
        }
        self.logger = logging.getLogger(__name__)
    
    def send_message(self, message: str, level: str = "INFO", 
                    attachments: Optional[List[Dict]] = None) -> bool:
        """メッセージを送信（attachments付き→失敗時はtextのみで再送）"""
        try:
            # attachmentsが指定されていればリッチ通知を試みる
            if attachments:
                payload = {
                    "text": message,
                    "attachments": attachments
                }
            else:
                payload = {"text": message}
            response = requests.post(
                self.config['webhook_url'],
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            self.logger.info(f"Slack notification sent: {level}")
            return True
        except Exception as e:
            self.logger.warning(f"Rich Slack notification failed, fallback to text only: {e}")
            # フォールバック: textのみで再送
            try:
                payload = {"text": message}
                response = requests.post(
                    self.config['webhook_url'],
                    json=payload,
                    timeout=10
                )
                response.raise_for_status()
                self.logger.info(f"Slack fallback notification sent: {level}")
                return True
            except Exception as e2:
                self.logger.error(f"Failed to send Slack notification (fallback): {e2}")
                return False
    
    def send_log_notification(self, log_entry: Dict) -> bool:
        """ログエントリを通知"""
        message = log_entry.get('message', 'No message')
        level = log_entry.get('level', 'INFO')
        service = log_entry.get('service', 'Unknown')
        timestamp = log_entry.get('timestamp')
        
        # メッセージの構築
        full_message = f"**{service}**\n{message}"
        
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                full_message += f"\n\n_Time: {dt.strftime('%Y-%m-%d %H:%M:%S UTC')}_"
            except ValueError:
                full_message += f"\n\n_Time: {timestamp}_"
        
        # アタッチメントの構築
        attachments = [{
            "color": self._get_color_for_level(level),
            "title": f"🚂 Railway Log - {level}",
            "text": full_message,
            "footer": "Price Comparison App",
            "ts": int(datetime.now().timestamp())
        }]
        
        return self.send_message(full_message, level, attachments)
    
    def send_batch_notification(self, log_entries: List[Dict]) -> bool:
        """複数のログエントリを一括通知"""
        if not log_entries:
            return True
        
        # 重要度の高いログを優先
        sorted_logs = sorted(log_entries, 
                           key=lambda x: self._get_priority(x.get('level', 'INFO')), 
                           reverse=True)
        
        # 最大5件まで通知
        logs_to_notify = sorted_logs[:5]
        
        success_count = 0
        for log_entry in logs_to_notify:
            if self.send_log_notification(log_entry):
                success_count += 1
        
        # 残りのログがある場合は要約通知
        if len(sorted_logs) > 5:
            summary = f"他 {len(sorted_logs) - 5} 件のログがあります"
            self.send_message(summary, "INFO")
        
        return success_count > 0
    
    def send_health_check(self, status: str, details: Optional[Dict] = None) -> bool:
        """ヘルスチェック結果を通知"""
        emoji_map = {
            'healthy': '✅',
            'unhealthy': '❌',
            'warning': '⚠️'
        }
        
        emoji = emoji_map.get(status, 'ℹ️')
        message = f"{emoji} Application Health Check: {status.upper()}"
        
        attachments = []
        if details:
            attachment = {
                "color": self._get_color_for_level(status),
                "title": "Health Check Details",
                "fields": []
            }
            
            for key, value in details.items():
                attachment["fields"].append({
                    "title": key.title(),
                    "value": str(value),
                    "short": True
                })
            
            attachments.append(attachment)
        
        return self.send_message(message, status, attachments)
    
    def _get_color_for_level(self, level: str) -> str:
        """ログレベルに応じた色を取得"""
        color_map = {
            "INFO": "#36a64f",      # 緑
            "WARNING": "#ff9500",   # オレンジ
            "WARN": "#ff9500",      # オレンジ
            "ERROR": "#ff0000",     # 赤
            "CRITICAL": "#8b0000",  # 濃い赤
            "healthy": "#36a64f",   # 緑
            "unhealthy": "#ff0000", # 赤
            "warning": "#ff9500"    # オレンジ
        }
        return color_map.get(level.upper(), "#36a64f")
    
    def _get_priority(self, level: str) -> int:
        """ログレベルの優先度を取得"""
        priority_map = {
            "CRITICAL": 4,
            "ERROR": 3,
            "WARN": 2,
            "WARNING": 2,
            "INFO": 1,
            "DEBUG": 0
        }
        return priority_map.get(level.upper(), 0) 