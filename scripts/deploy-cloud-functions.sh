#!/bin/bash

# Cloud Functions 一括デプロイスクリプト
# 使用方法: ./scripts/deploy-cloud-functions.sh

set -e

# 設定
PROJECT_ID="price-comparison-app"
REGION="asia-northeast1"
RUNTIME="python311"

echo "🚀 Cloud Functions 一括デプロイを開始します..."
echo "プロジェクト: $PROJECT_ID"
echo "リージョン: $REGION"
echo "ランタイム: $RUNTIME"
echo ""

# 関数一覧
FUNCTIONS=(
    "get_prices"
    "get_price_history"
    "api_prices"
    "api_status"
    "health"
    "scrape_prices"
    "set_alert"
    "check_prices"
)

# 各関数をデプロイ
for func in "${FUNCTIONS[@]}"; do
    echo "📦 $func をデプロイ中..."
    
    cd "functions/$func"
    
    gcloud functions deploy "$func" \
        --runtime "$RUNTIME" \
        --trigger-http \
        --allow-unauthenticated \
        --entry-point "$func" \
        --region "$REGION" \
        --project "$PROJECT_ID"
    
    echo "✅ $func のデプロイが完了しました"
    echo ""
    
    cd ../..
done

echo "🎉 全Cloud Functionsのデプロイが完了しました！"
echo ""
echo "📋 デプロイされた関数一覧:"
for func in "${FUNCTIONS[@]}"; do
    echo "  - $func: https://$REGION-$PROJECT_ID.cloudfunctions.net/$func"
done 