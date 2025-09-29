#!/usr/bin/env python3
"""
詳細なAPIテストスクリプト
各エンドポイントの機能を詳細にテストする

このスクリプトは以下の機能を提供します:
- 各エンドポイントの詳細な動作確認
- レスポンスデータの構造検証
- エラーハンドリングの確認
- データの整合性チェック
"""

import json
import sys
import time
from typing import Any, Dict, List, Optional

import requests

# Cloud Functions のベースURL
BASE_URL = "https://asia-northeast1-price-comparison-app-463007.cloudfunctions.net"

class DetailedAPITester:
    def __init__(self):
        self.results = []
        self.failed_tests = []
        
    def test_health_endpoint(self) -> bool:
        """ヘルスチェックエンドポイントの詳細テスト"""
        print("🏥 Testing Health Endpoint")
        print("-" * 40)
        
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Status: {response.status_code}")
                print(f"✅ Response: {data}")
                
                # 期待されるフィールドの確認
                required_fields = ["status", "timestamp"]
                for field in required_fields:
                    if field in data:
                        print(f"✅ Field '{field}': {data[field]}")
                    else:
                        print(f"❌ Missing field: {field}")
                        return False
                
                if data.get("status") == "healthy":
                    print("✅ Health status is healthy")
                    return True
                else:
                    print(f"❌ Health status is not healthy: {data.get('status')}")
                    return False
            else:
                print(f"❌ Status: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return False
    
    def test_api_status_endpoint(self) -> bool:
        """APIステータスエンドポイントの詳細テスト"""
        print("\n📊 Testing API Status Endpoint")
        print("-" * 40)
        
        try:
            response = requests.get(f"{BASE_URL}/api_status", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Status: {response.status_code}")
                print(f"✅ Response: {data}")
                
                # 期待されるフィールドの確認
                if isinstance(data, dict):
                    print(f"✅ Response is a dictionary with {len(data)} keys")
                    
                    # 各サービスのステータスを確認
                    for service, status in data.items():
                        if isinstance(status, dict) and "status" in status:
                            print(f"✅ {service}: {status['status']}")
                        else:
                            print(f"✅ {service}: {status}")
                else:
                    print(f"✅ Response format: {type(data)}")
                    print(f"✅ Response content: {data}")
                
                return True
            else:
                print(f"❌ Status: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return False
    
    def test_get_prices_endpoint(self) -> bool:
        """価格取得エンドポイントの詳細テスト"""
        print("\n💰 Testing Get Prices Endpoint")
        print("-" * 40)
        
        # テストするシリーズ
        test_series = ["iPhone 17", "iPhone 17 Pro", "iPhone 17 Pro Max"]
        
        for series in test_series:
            print(f"\n🔍 Testing series: {series}")
            try:
                response = requests.get(
                    f"{BASE_URL}/get_prices",
                    params={"series": series},
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Status: {response.status_code}")
                    print(f"✅ Found {len(data)} records for {series}")
                    
                    if isinstance(data, list) and len(data) > 0:
                        # 最初のレコードの構造を確認
                        first_record = data[0]
                        print(f"✅ Sample record: {first_record}")
                        
                        # 必要なフィールドの確認
                        required_fields = ["series", "capacity", "kaitori_price_min", "kaitori_price_max"]
                        for field in required_fields:
                            if field in first_record:
                                print(f"✅ Field '{field}': {first_record[field]}")
                            else:
                                print(f"❌ Missing field: {field}")
                                return False
                    else:
                        print(f"⚠️  No data returned for {series}")
                else:
                    print(f"❌ Status: {response.status_code}")
                    print(f"Response: {response.text}")
                    return False
                    
            except Exception as e:
                print(f"❌ Error testing {series}: {str(e)}")
                return False
        
        return True
    
    def test_api_prices_endpoint(self) -> bool:
        """公式価格取得エンドポイントの詳細テスト"""
        print("\n🏪 Testing API Prices Endpoint")
        print("-" * 40)
        
        try:
            response = requests.get(f"{BASE_URL}/api_prices", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Status: {response.status_code}")
                print(f"✅ Found {len(data)} official price series")
                
                if isinstance(data, list):
                    print(f"✅ Found {len(data)} official price series (list format)")
                    
                    # iPhone 17シリーズの確認
                    iphone17_series = [item for item in data if "iPhone 17" in str(item)]
                    print(f"✅ iPhone 17 series found: {len(iphone17_series)} items")
                    
                    if len(iphone17_series) > 0:
                        # 最初のiPhone 17シリーズの詳細を確認
                        first_series = iphone17_series[0]
                        print(f"✅ Sample series: {first_series}")
                elif isinstance(data, dict):
                    print(f"✅ Found {len(data)} official price series (dictionary format)")
                    
                    # iPhone 17シリーズの確認
                    iphone17_series = [key for key in data.keys() if "iPhone 17" in key]
                    print(f"✅ iPhone 17 series found: {iphone17_series}")
                    
                    if len(iphone17_series) > 0:
                        # 最初のiPhone 17シリーズの詳細を確認
                        first_series = iphone17_series[0]
                        series_data = data[first_series]
                        print(f"✅ Sample series ({first_series}): {series_data}")
                else:
                    print(f"✅ Response format: {type(data)}")
                    print(f"✅ Response content: {data}")
                
                return True
            else:
                print(f"❌ Status: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return False
    
    def test_get_price_history_endpoint(self) -> bool:
        """価格履歴取得エンドポイントの詳細テスト"""
        print("\n📈 Testing Get Price History Endpoint")
        print("-" * 40)
        
        # テストするパラメータ
        test_params = [
            {"series": "iPhone 17", "capacity": "256GB"},
            {"series": "iPhone 17 Pro", "capacity": "512GB"},
        ]
        
        for params in test_params:
            print(f"\n🔍 Testing: {params}")
            try:
                response = requests.get(
                    f"{BASE_URL}/get_price_history",
                    params=params,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Status: {response.status_code}")
                    print(f"✅ Found {len(data)} history records")
                    
                    if isinstance(data, list):
                        if len(data) > 0:
                            # 最初のレコードの構造を確認
                            first_record = data[0]
                            print(f"✅ Sample record: {first_record}")
                            
                            # 必要なフィールドの確認
                            required_fields = ["timestamp", "kaitori_price_min", "kaitori_price_max"]
                            for field in required_fields:
                                if field in first_record:
                                    print(f"✅ Field '{field}': {first_record[field]}")
                                else:
                                    print(f"❌ Missing field: {field}")
                                    return False
                        else:
                            print(f"⚠️  No history data for {params}")
                    elif isinstance(data, dict):
                        print(f"✅ Response is a dictionary: {data}")
                        # 辞書形式の場合も受け入れる
                    else:
                        print(f"✅ Response format: {type(data)}")
                        print(f"✅ Response content: {data}")
                else:
                    print(f"❌ Status: {response.status_code}")
                    print(f"Response: {response.text}")
                    return False
                    
            except Exception as e:
                print(f"❌ Error testing {params}: {str(e)}")
                return False
        
        return True
    
    def run_all_tests(self) -> bool:
        """すべての詳細テストを実行"""
        print("🔍 Detailed API Test Suite")
        print("=" * 60)
        
        tests = [
            ("Health Endpoint", self.test_health_endpoint),
            ("API Status Endpoint", self.test_api_status_endpoint),
            ("Get Prices Endpoint", self.test_get_prices_endpoint),
            ("API Prices Endpoint", self.test_api_prices_endpoint),
            ("Get Price History Endpoint", self.test_get_price_history_endpoint),
        ]
        
        all_passed = True
        
        for test_name, test_func in tests:
            print(f"\n{'='*60}")
            print(f"🧪 {test_name}")
            print(f"{'='*60}")
            
            try:
                success = test_func()
                self.results.append({
                    "name": test_name,
                    "success": success
                })
                
                if success:
                    print(f"✅ {test_name}: PASSED")
                else:
                    print(f"❌ {test_name}: FAILED")
                    self.failed_tests.append(test_name)
                    all_passed = False
                    
            except Exception as e:
                print(f"❌ {test_name}: ERROR - {str(e)}")
                self.results.append({
                    "name": test_name,
                    "success": False
                })
                self.failed_tests.append(test_name)
                all_passed = False
        
        return all_passed
    
    def print_summary(self):
        """テスト結果のサマリーを表示"""
        print(f"\n{'='*60}")
        print("📊 Detailed Test Summary")
        print(f"{'='*60}")
        
        passed = sum(1 for result in self.results if result["success"])
        total = len(self.results)
        
        print(f"✅ Passed: {passed}/{total}")
        
        if self.failed_tests:
            print(f"❌ Failed: {', '.join(self.failed_tests)}")
        else:
            print("🎉 All detailed tests passed!")
        
        print()
        
        # 詳細結果
        for result in self.results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['name']}")

def main():
    """メイン関数"""
    print("🔍 Detailed Cloud Functions API Test Suite")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}")
    print()
    
    tester = DetailedAPITester()
    
    # すべてのテストを実行
    all_passed = tester.run_all_tests()
    
    # サマリーを表示
    tester.print_summary()
    
    # 終了コードを設定
    if all_passed:
        print("\n🎉 All detailed API tests completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some detailed API tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
