#!/bin/bash

# Railway → Cloud Run 移行前環境調査スクリプト
echo "🔍 Railway → Cloud Run 移行前環境調査を開始します..."

# 1. 現在のRailway環境の確認
echo "📊 現在のRailway環境:"
echo "Service ID: $RAILWAY_SERVICE_ID"
echo "Service Name: price-comparison-app"

# 2. プロジェクト構造の確認
echo "📁 プロジェクト構造:"
echo "Frontend: $(ls -la frontend/ | wc -l) files"
echo "Backend: $(ls -la backend/ | wc -l) files"
echo "Templates: $(ls -la templates/ 2>/dev/null | wc -l || echo "0") files"

# 3. 依存関係の確認
echo "📦 依存関係:"
echo "Frontend dependencies: $(cat frontend/package.json | jq '.dependencies | keys | length')"
echo "Backend dependencies: $(wc -l < backend/requirements.txt)"

# 4. 環境変数の確認
echo "🔧 環境変数:"
echo "BUCKET_NAME: $BUCKET_NAME"
echo "APP_ENV: $APP_ENV"
echo "SECRET_KEY: ${SECRET_KEY:0:10}..."

# 5. 現在のデプロイ設定
echo "🚀 デプロイ設定:"
echo "Railway config: $(cat railway.json | jq '.')"
echo "Dockerfile: $(wc -l < Dockerfile) lines"
echo "Procfile: $(cat Procfile)"

# 6. データストレージの確認
echo "💾 データストレージ:"
if [ -n "$BUCKET_NAME" ]; then
    echo "Cloud Storage bucket: $BUCKET_NAME"
    gsutil ls gs://$BUCKET_NAME/ 2>/dev/null || echo "Bucket not accessible"
else
    echo "No Cloud Storage bucket configured"
fi

echo "✅ 環境調査完了" 