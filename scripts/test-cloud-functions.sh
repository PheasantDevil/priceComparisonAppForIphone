#!/bin/bash

# Cloud Functions テストスクリプト
# 使用方法: ./scripts/test-cloud-functions.sh

set -e

# 設定
BASE_URL="https://asia-northeast1-price-comparison-app.cloudfunctions.net"

echo "🧪 Cloud Functions テストを開始します..."
echo "ベースURL: $BASE_URL"
echo ""

# テスト関数一覧
declare -A TESTS=(
    ["health"]="GET"
    ["api_status"]="GET"
    ["get_prices"]="GET?series=iPhone15"
    ["get_price_history"]="GET?series=iPhone15&capacity=128GB&days=7"
    ["api_prices"]="GET"
    ["check_prices"]="GET"
)

# 各関数をテスト
for func in "${!TESTS[@]}"; do
    method="${TESTS[$func]}"
    url="$BASE_URL/$func"
    
    if [[ $method == GET* ]]; then
        # GETリクエスト（クエリパラメータがある場合）
        if [[ $method == *"?"* ]]; then
            query="${method#GET}"
            url="$url$query"
        fi
        
        echo "🔍 $func をテスト中... ($url)"
        response=$(curl -s -w "%{http_code}" "$url")
        http_code="${response: -3}"
        body="${response%???}"
        
        if [ "$http_code" -eq 200 ]; then
            echo "✅ $func: HTTP $http_code - 成功"
        else
            echo "❌ $func: HTTP $http_code - 失敗"
            echo "   レスポンス: $body"
        fi
    else
        echo "⚠️  $func: 未実装のメソッド ($method)"
    fi
    
    echo ""
done

echo "🎯 テスト完了！" 