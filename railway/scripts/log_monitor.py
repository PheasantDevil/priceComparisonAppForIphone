#!/usr/bin/env python3
"""
Railwayログ監視スクリプト
Railwayのログを監視してSlackに送信する
"""

import argparse
import logging
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List

# プロジェクトルートをパスに追加
sys.path.append('.')

from railway.config.settings import (log_monitor_config, railway_config,
                                     slack_config, validate_configs)
from railway.utils.railway_client import RailwayClient
from railway.utils.slack_notifier import SlackNotifier


class RailwayLogMonitor:
    """Railwayログ監視クラス"""
    
    def __init__(self):
        self.railway_client = RailwayClient()
        self.slack_notifier = SlackNotifier()
        self.logger = logging.getLogger(__name__)
        self.last_log_time = None
        self.last_notification_time = None
    
    def should_notify(self, log_entry: Dict) -> bool:
        """通知すべきログかどうかを判定"""
        message = log_entry.get('message', '').lower()
        level = log_entry.get('level', 'INFO').upper()
        
        # 設定されたログレベルをチェック
        if level in log_monitor_config.log_levels:
            return True
        
        # 重要なキーワードをチェック
        return any(keyword.lower() in message 
                  for keyword in log_monitor_config.important_keywords)
    
    def filter_new_logs(self, logs: List[Dict]) -> List[Dict]:
        """新しいログのみをフィルタリング"""
        if not self.last_log_time:
            # 初回実行時は最新のログのみを取得
            if logs:
                self.last_log_time = logs[-1].get('timestamp')
            return logs[-log_monitor_config.max_logs_per_batch:] if len(logs) > log_monitor_config.max_logs_per_batch else logs
        
        new_logs = []
        for log in logs:
            log_time = log.get('timestamp')
            if log_time and log_time > self.last_log_time:
                new_logs.append(log)
        
        if new_logs:
            self.last_log_time = new_logs[-1].get('timestamp')
        
        return new_logs
    
    def monitor_logs(self, interval: int = None, single_run: bool = False):
        """ログを継続的に監視"""
        interval = interval or log_monitor_config.interval
        
        self.logger.info(f"Starting Railway log monitoring (interval: {interval}s)")
        self.logger.info(f"Slack channel: {slack_config.channel}")
        self.logger.info(f"Project ID: {railway_config.project_id}")
        
        # Railway CLIの可用性をチェック
        if not self.railway_client.is_cli_available():
            self.logger.error("Railway CLI is not available")
            return False
        
        # ログインが必要かチェック
        if not self.railway_client.login_if_needed():
            self.logger.error("Failed to login to Railway")
            return False
        
        try:
            while True:
                try:
                    # ログを取得
                    logs = self.railway_client.get_logs(
                        limit=log_monitor_config.max_logs_per_batch
                    )
                    
                    if not logs:
                        self.logger.debug("No logs retrieved")
                        if single_run:
                            break
                        time.sleep(interval)
                        continue
                    
                    # 新しいログをフィルタリング
                    new_logs = self.filter_new_logs(logs)
                    
                    if new_logs:
                        self.logger.info(f"Found {len(new_logs)} new logs")
                        
                        # 通知すべきログをフィルタリング
                        logs_to_notify = [
                            log for log in new_logs 
                            if self.should_notify(log)
                        ]
                        
                        if logs_to_notify:
                            self.logger.info(f"Sending {len(logs_to_notify)} notifications")
                            self.slack_notifier.send_batch_notification(logs_to_notify)
                        else:
                            self.logger.debug("No logs to notify")
                    else:
                        self.logger.debug("No new logs found")
                    
                    if single_run:
                        break
                    
                    time.sleep(interval)
                    
                except KeyboardInterrupt:
                    self.logger.info("Stopping log monitoring...")
                    break
                except Exception as e:
                    self.logger.error(f"Error in monitoring loop: {e}")
                    if single_run:
                        break
                    time.sleep(interval)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Fatal error in monitoring: {e}")
            return False
    
    def send_health_check(self) -> bool:
        """ヘルスチェックを実行してSlackに通知"""
        try:
            # プロジェクト情報を取得
            project_info = self.railway_client.get_project_info()
            
            if not project_info:
                self.slack_notifier.send_health_check('unhealthy', {
                    'error': 'Failed to get project info'
                })
                return False
            
            # サービス情報を取得
            services = project_info.get('services', [])
            service_statuses = {}
            
            for service in services:
                service_id = service.get('id')
                if service_id:
                    service_info = self.railway_client.get_service_info(service_id)
                    if service_info:
                        service_statuses[service.get('name', service_id)] = {
                            'status': service_info.get('status', 'unknown'),
                            'url': service_info.get('url', 'N/A')
                        }
            
            # ヘルスチェック結果を判定
            overall_status = 'healthy'
            if not services:
                overall_status = 'unhealthy'
            elif any(s.get('status') != 'running' for s in service_statuses.values()):
                overall_status = 'warning'
            
            # Slackに通知
            details = {
                'project': project_info.get('name', 'Unknown'),
                'services': len(services),
                'environment': railway_config.environment
            }
            
            return self.slack_notifier.send_health_check(overall_status, details)
            
        except Exception as e:
            self.logger.error(f"Error in health check: {e}")
            self.slack_notifier.send_health_check('unhealthy', {'error': str(e)})
            return False


def setup_logging(level: str = 'INFO'):
    """ログ設定を初期化"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('railway/logs/monitor.log')
        ]
    )


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='Railway Log Monitor')
    parser.add_argument('--single-run', action='store_true',
                       help='Run once and exit (for GitHub Actions)')
    parser.add_argument('--interval', type=int, default=None,
                       help='Monitoring interval in seconds')
    parser.add_argument('--health-check', action='store_true',
                       help='Run health check only')
    parser.add_argument('--log-level', default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Log level')
    
    args = parser.parse_args()
    
    # ログ設定
    setup_logging(args.log_level)
    
    # 設定の妥当性を検証
    if not validate_configs():
        sys.exit(1)
    
    try:
        monitor = RailwayLogMonitor()
        
        if args.health_check:
            # ヘルスチェックのみ実行
            success = monitor.send_health_check()
            sys.exit(0 if success else 1)
        else:
            # ログ監視を実行
            success = monitor.monitor_logs(
                interval=args.interval,
                single_run=args.single_run
            )
            sys.exit(0 if success else 1)
            
    except Exception as e:
        logging.error(f"Failed to start monitor: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 