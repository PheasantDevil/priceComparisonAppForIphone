#!/usr/bin/env python3
"""
Slack通知テストスクリプト
"""

import sys
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.append('.')

from railway.config.settings import validate_configs
from railway.utils.slack_notifier import SlackNotifier


def test_basic_notification():
    """基本的な通知テスト"""
    print("🧪 基本的な通知テスト")
    
    notifier = SlackNotifier()
    message = f"🚂 Railway Log Monitor テスト通知\n時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    success = notifier.send_message(message, "INFO")
    if success:
        print("✅ 基本的な通知テストが成功しました")
        return True
    else:
        print("❌ 基本的な通知テストが失敗しました")
        return False


def test_error_notification():
    """エラー通知テスト"""
    print("🧪 エラー通知テスト")
    
    notifier = SlackNotifier()
    message = f"🚨 Railway Log Monitor エラーテスト\n時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    success = notifier.send_message(message, "ERROR")
    if success:
        print("✅ エラー通知テストが成功しました")
        return True
    else:
        print("❌ エラー通知テストが失敗しました")
        return False


def test_health_check():
    """ヘルスチェック通知テスト"""
    print("🧪 ヘルスチェック通知テスト")
    
    notifier = SlackNotifier()
    details = {
        'project': 'Price Comparison App',
        'services': 1,
        'environment': 'production',
        'status': 'healthy'
    }
    
    success = notifier.send_health_check('healthy', details)
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
        return False
    
    print("✅ 設定の妥当性確認が完了しました")
    print()
    
    # テスト実行
    tests = [
        test_basic_notification,
        test_error_notification,
        test_health_check
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
            print()
        except Exception as e:
            print(f"❌ テスト実行中にエラーが発生しました: {e}")
            results.append(False)
            print()
    
    # 結果表示
    print("📊 テスト結果")
    print("=" * 20)
    success_count = sum(results)
    total_count = len(results)
    
    print(f"成功: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("🎉 全てのテストが成功しました！")
        print("Railway Log Monitorが正常に動作しています。")
        return True
    else:
        print("⚠️ 一部のテストが失敗しました。")
        print("設定を確認してください。")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 