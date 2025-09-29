#!/usr/bin/env python3
"""
Cloud Functions API エンドポイントのテストスクリプト
functionsディレクトリが更新された時にAPIの動作を確認する
"""

import json
import requests
import sys
import time
from typing import Dict, List, Optional

# Cloud Functions のベースURL
BASE_URL = "https://asia-northeast1-price-comparison-app-463007.cloudfunctions.net"

# テスト対象のエンドポイント
ENDPOINTS = {
    "health": {
        "url": f"{BASE_URL}/health",
        "method": "GET",
        "expected_status": 200,
        "description": "ヘルスチェック"
    },
    "api_status": {
        "url": f"{BASE_URL}/api_status",
        "method": "GET", 
        "expected_status": 200,
        "description": "APIステータス確認"
    },
    "get_prices": {
        "url": f"{BASE_URL}/get_prices",
        "method": "GET",
        "params": {"series": "iPhone 17"},
        "expected_status": 200,
        "description": "価格データ取得"
    },
    "get_price_history": {
        "url": f"{BASE_URL}/get_price_history",
        "method": "GET",
        "params": {"series": "iPhone 17", "capacity": "256GB"},
        "expected_status": 200,
        "description": "価格履歴取得"
    },
    "api_prices": {
        "url": f"{BASE_URL}/api_prices",
        "method": "GET",
        "expected_status": 200,
        "description": "公式価格取得"
    }
}

class APITester:
    def __init__(self):
        self.results = []
        self.failed_tests = []
        
    def test_endpoint(self, name: str, config: Dict) -> bool:
        """個別のエンドポイントをテスト"""
        print(f"🧪 Testing {name}: {config['description']}")
        
        try:
            # リクエスト送信
            if config["method"] == "GET":
                response = requests.get(
                    config["url"], 
                    params=config.get("params", {}),
                    timeout=30
                )
            else:
                response = requests.request(
                    config["method"],
                    config["url"],
                    json=config.get("data", {}),
                    timeout=30
                )
            
            # ステータスコード確認
            if response.status_code == config["expected_status"]:
                print(f"  ✅ Status: {response.status_code}")
                
                # レスポンス内容の基本確認
                try:
                    data = response.json()
                    print(f"  ✅ Response: Valid JSON")
                    
                    # 各エンドポイント固有のチェック
                    if name == "health":
                        if "status" in data and data["status"] == "healthy":
                            print(f"  ✅ Health check passed")
                        else:
                            print(f"  ⚠️  Health check response unexpected: {data}")
                            
                    elif name == "get_prices":
                        if isinstance(data, list) and len(data) > 0:
                            print(f"  ✅ Found {len(data)} price records")
                            # iPhone 17シリーズが含まれているかチェック
                            has_iphone17 = any("iPhone 17" in str(record) for record in data)
                            if has_iphone17:
                                print(f"  ✅ iPhone 17 series found in results")
                            else:
                                print(f"  ⚠️  iPhone 17 series not found in results")
                        else:
                            print(f"  ⚠️  No price data returned")
                            
                    elif name == "api_prices":
                        if isinstance(data, dict) and len(data) > 0:
                            print(f"  ✅ Found {len(data)} official price series")
                            # iPhone 17シリーズが含まれているかチェック
                            has_iphone17 = any("iPhone 17" in series for series in data.keys())
                            if has_iphone17:
                                print(f"  ✅ iPhone 17 series found in official prices")
                            else:
                                print(f"  ⚠️  iPhone 17 series not found in official prices")
                        else:
                            print(f"  ⚠️  No official price data returned")
                            
                    elif name == "get_price_history":
                        if isinstance(data, list):
                            print(f"  ✅ Found {len(data)} price history records")
                        else:
                            print(f"  ⚠️  Price history data format unexpected")
                            
                except json.JSONDecodeError:
                    print(f"  ⚠️  Response is not valid JSON")
                    print(f"  Response content: {response.text[:200]}...")
                
                return True
            else:
                print(f"  ❌ Status: {response.status_code} (expected {config['expected_status']})")
                print(f"  Response: {response.text[:200]}...")
                return False
                
        except requests.exceptions.Timeout:
            print(f"  ❌ Timeout after 30 seconds")
            return False
        except requests.exceptions.ConnectionError:
            print(f"  ❌ Connection error")
            return False
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            return False
    
    def run_all_tests(self) -> bool:
        """すべてのテストを実行"""
        print("🚀 Starting API endpoint tests...")
        print("=" * 60)
        
        all_passed = True
        
        for name, config in ENDPOINTS.items():
            success = self.test_endpoint(name, config)
            self.results.append({
                "name": name,
                "description": config["description"],
                "success": success
            })
            
            if not success:
                all_passed = False
                self.failed_tests.append(name)
            
            print()  # 空行を追加
        
        return all_passed
    
    def print_summary(self):
        """テスト結果のサマリーを表示"""
        print("📊 Test Summary")
        print("=" * 60)
        
        passed = sum(1 for result in self.results if result["success"])
        total = len(self.results)
        
        print(f"✅ Passed: {passed}/{total}")
        
        if self.failed_tests:
            print(f"❌ Failed: {', '.join(self.failed_tests)}")
        else:
            print("🎉 All tests passed!")
        
        print()
        
        # 詳細結果
        for result in self.results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['name']}: {result['description']}")

def main():
    """メイン関数"""
    print("🔍 Cloud Functions API Test Suite")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}")
    print()
    
    tester = APITester()
    
    # すべてのテストを実行
    all_passed = tester.run_all_tests()
    
    # サマリーを表示
    tester.print_summary()
    
    # 終了コードを設定
    if all_passed:
        print("🎉 All API tests completed successfully!")
        sys.exit(0)
    else:
        print("❌ Some API tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
