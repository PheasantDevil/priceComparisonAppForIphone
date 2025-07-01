#!/usr/bin/env python3
"""
Slack通知テストスクリプト
"""

import os
import sys

# プロジェクトルートをパスに追加
sys.path.append('.')

from railway import SlackNotifier, validate_configs


def test_basic_notification():
    """基本的な通知テスト"""
    print("🧪 基本的な通知テスト")
    
    if not validate_configs():
        print("❌ 設定の妥当性確認に失敗しました")
        return False
    
    slack_notifier = SlackNotifier()
    
    success = slack_notifier.send_message(
        "🚂 Railway Log Monitor テスト通知",
        "INFO",
        attachments=[{
            "color": "#36a64f",
            "title": "テスト通知",
            "text": "これはテスト通知です。Railway Log Monitorが正常に動作しています。",
            "fields": [
                {
                    "title": "テストタイプ",
                    "value": "基本通知",
                    "short": True
                },
                {
                    "title": "ステータス",
                    "value": "✅ 成功",
                    "short": True
                }
            ]
        }]
    )
    
    if success:
        print("✅ 基本的な通知テストが成功しました")
        return True
    else:
        print("❌ 基本的な通知テストが失敗しました")
        return False


def test_error_notification():
    """エラー通知テスト"""
    print("🧪 エラー通知テスト")
    
    if not validate_configs():
        print("❌ 設定の妥当性確認に失敗しました")
        return False
    
    slack_notifier = SlackNotifier()
    
    success = slack_notifier.send_message(
        "❌ テストエラー通知",
        "ERROR",
        attachments=[{
            "color": "#ff0000",
            "title": "テストエラー",
            "text": "これはテスト用のエラー通知です。実際のエラーではありません。",
            "fields": [
                {
                    "title": "エラータイプ",
                    "value": "テストエラー",
                    "short": True
                },
                {
                    "title": "重要度",
                    "value": "低",
                    "short": True
                }
            ]
        }]
    )
    
    if success:
        print("✅ エラー通知テストが成功しました")
        return True
    else:
        print("❌ エラー通知テストが失敗しました")
        return False


def test_health_check():
    """ヘルスチェック通知テスト"""
    print("🧪 ヘルスチェック通知テスト")
    
    if not validate_configs():
        print("❌ 設定の妥当性確認に失敗しました")
        return False
    
    slack_notifier = SlackNotifier()
    
    success = slack_notifier.send_health_check('healthy', {
        'project': 'Price Comparison App',
        'services': 1,
        'environment': 'production',
        'test': True
    })
    
    if success:
        print("✅ ヘルスチェック通知テストが成功しました")
        return True
    else:
        print("❌ ヘルスチェック通知テストが失敗しました")
        return False


def main():
    """メイン関数"""
    print("🚂 Railway Log Monitor - Slack通知テスト")
    print("=" * 50)
    
    # 設定の妥当性を確認
    print("🔍 設定の妥当性を確認中...")
    if not validate_configs():
        print("❌ 設定の妥当性確認に失敗しました")
        print("環境変数が正しく設定されているか確認してください")
        sys.exit(1)
    
    print("✅ 設定の妥当性確認が完了しました")
    print()
    
    # 各テストを実行
    tests = [
        test_basic_notification,
        test_error_notification,
        test_health_check
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ テスト実行中にエラーが発生しました: {e}")
        print()
    
    # 結果を表示
    print("📊 テスト結果")
    print("=" * 20)
    print(f"成功: {passed}/{total}")
    
    if passed == total:
        print("🎉 全てのテストが成功しました！")
        print("Railway Log Monitorが正常に動作しています。")
        sys.exit(0)
    else:
        print("⚠️  一部のテストが失敗しました")
        print("設定を確認してください。")
        sys.exit(1)


if __name__ == "__main__":
    main() 