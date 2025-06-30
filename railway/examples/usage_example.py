"""
既存アプリケーションからRailwayユーティリティを利用する例
"""

import os
import sys

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from railway import RailwayClient, SlackNotifier, validate_configs


def example_health_check():
    """ヘルスチェックの例"""
    print("=== Railway Health Check Example ===")
    
    # 設定の妥当性を検証
    if not validate_configs():
        print("Configuration validation failed")
        return
    
    # Railwayクライアントを作成
    railway_client = RailwayClient()
    
    # プロジェクト情報を取得
    project_info = railway_client.get_project_info()
    if project_info:
        print(f"Project: {project_info.get('name', 'Unknown')}")
        print(f"Services: {len(project_info.get('services', []))}")
    else:
        print("Failed to get project info")
    
    # Slack通知を送信
    slack_notifier = SlackNotifier()
    success = slack_notifier.send_health_check('healthy', {
        'project': project_info.get('name', 'Unknown') if project_info else 'Unknown',
        'services': len(project_info.get('services', [])) if project_info else 0
    })
    
    print(f"Health check notification sent: {success}")


def example_log_monitoring():
    """ログ監視の例"""
    print("=== Railway Log Monitoring Example ===")
    
    # 設定の妥当性を検証
    if not validate_configs():
        print("Configuration validation failed")
        return
    
    # Railwayクライアントを作成
    railway_client = RailwayClient()
    
    # 最新のログを取得
    logs = railway_client.get_logs(limit=10)
    print(f"Retrieved {len(logs)} logs")
    
    # 重要なログをフィルタリング
    important_logs = []
    for log in logs:
        message = log.get('message', '').lower()
        level = log.get('level', 'INFO').upper()
        
        # エラーログまたは重要なキーワードを含むログ
        if (level in ['ERROR', 'WARN', 'CRITICAL'] or
            any(keyword in message for keyword in ['error', 'failed', 'timeout'])):
            important_logs.append(log)
    
    if important_logs:
        print(f"Found {len(important_logs)} important logs")
        
        # Slackに通知
        slack_notifier = SlackNotifier()
        success = slack_notifier.send_batch_notification(important_logs)
        print(f"Notifications sent: {success}")
    else:
        print("No important logs found")


def example_custom_notification():
    """カスタム通知の例"""
    print("=== Custom Notification Example ===")
    
    # 設定の妥当性を検証
    if not validate_configs():
        print("Configuration validation failed")
        return
    
    # Slack通知を作成
    slack_notifier = SlackNotifier()
    
    # カスタムメッセージを送信
    success = slack_notifier.send_message(
        "🚀 Application deployment completed successfully!",
        "INFO",
        attachments=[{
            "color": "#36a64f",
            "title": "Deployment Status",
            "text": "The application has been deployed successfully to Railway.",
            "fields": [
                {
                    "title": "Environment",
                    "value": "Production",
                    "short": True
                },
                {
                    "title": "Status",
                    "value": "✅ Success",
                    "short": True
                }
            ]
        }]
    )
    
    print(f"Custom notification sent: {success}")


if __name__ == "__main__":
    print("Railway Utilities Usage Examples")
    print("=" * 40)
    
    # 各例を実行
    example_health_check()
    print()
    
    example_log_monitoring()
    print()
    
    example_custom_notification()
    print()
    
    print("Examples completed!") 