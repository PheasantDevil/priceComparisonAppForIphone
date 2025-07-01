#!/usr/bin/env python3
"""
Slack Webhook デバッグスクリプト
"""

import json

import requests


def test_simple_webhook():
    """シンプルなWebhookテスト"""
    webhook_url = "https://hooks.slack.com/services/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"
    
    # シンプルなメッセージ
    payload = {
        "text": "🚂 Railway Log Monitor テスト通知"
    }
    
    print("🧪 シンプルなWebhookテスト")
    print(f"URL: {webhook_url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ シンプルなWebhookテストが成功しました")
            return True
        else:
            print(f"❌ シンプルなWebhookテストが失敗しました: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        return False

def test_attachments_webhook():
    """アタッチメント付きWebhookテスト"""
    webhook_url = "https://hooks.slack.com/services/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"
    
    # アタッチメント付きメッセージ
    payload = {
        "text": "🚂 Railway Log Monitor テスト通知",
        "attachments": [
            {
                "color": "#36a64f",
                "title": "テスト通知",
                "text": "これはテスト通知です。",
                "fields": [
                    {
                        "title": "テストタイプ",
                        "value": "アタッチメント付き",
                        "short": True
                    }
                ]
            }
        ]
    }
    
    print("\n🧪 アタッチメント付きWebhookテスト")
    print(f"URL: {webhook_url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ アタッチメント付きWebhookテストが成功しました")
            return True
        else:
            print(f"❌ アタッチメント付きWebhookテストが失敗しました: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        return False

def test_full_webhook():
    """完全なWebhookテスト（ユーザー名、アイコン付き）"""
    webhook_url = "https://hooks.slack.com/services/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"
    
    # 完全なメッセージ
    payload = {
        "text": "🚂 Railway Log Monitor テスト通知",
        "username": "Railway Log Monitor",
        "icon_emoji": ":steam_locomotive:",
        "attachments": [
            {
                "color": "#36a64f",
                "title": "テスト通知",
                "text": "これはテスト通知です。",
                "fields": [
                    {
                        "title": "テストタイプ",
                        "value": "完全な通知",
                        "short": True
                    }
                ]
            }
        ]
    }
    
    print("\n🧪 完全なWebhookテスト")
    print(f"URL: {webhook_url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ 完全なWebhookテストが成功しました")
            return True
        else:
            print(f"❌ 完全なWebhookテストが失敗しました: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        return False

def main():
    """メイン関数"""
    print("🚂 Slack Webhook デバッグテスト")
    print("=" * 40)
    
    tests = [
        test_simple_webhook,
        test_attachments_webhook,
        test_full_webhook
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
    
    print("📊 テスト結果")
    print("=" * 20)
    print(f"成功: {passed}/{total}")
    
    if passed == total:
        print("🎉 全てのテストが成功しました！")
    else:
        print("⚠️  一部のテストが失敗しました")

if __name__ == "__main__":
    main() 