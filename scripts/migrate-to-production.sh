#!/bin/bash

# Railway → Cloud Run 本番移行スクリプト
set -e

source .env.gcp

SERVICE_NAME="price-comparison-app"
PRODUCTION_TAG="v1.0.0-$(date +%Y%m%d)"

echo "🚀 Railway → Cloud Run 本番移行を開始します..."

# 1. 現在のRailway環境の確認
echo "📊 現在のRailway環境を確認中..."
RAILWAY_URL=$(railway status | grep -o 'https://[^[:space:]]*' | head -1 || echo "https://price-comparison-app-production.up.railway.app")
echo "Railway URL: $RAILWAY_URL"

# 2. フロントエンドビルド
echo "🔨 フロントエンドビルド中..."
cd frontend
npm ci
npm run build
cd ..

# templatesディレクトリの準備
rm -rf templates
mkdir -p templates
cp -r frontend/out/* templates/

echo "✅ フロントエンドビルド完了"

# 3. 本番用Dockerイメージのビルド
echo "🐳 本番用Dockerイメージビルド中..."
gcloud builds submit \
    --tag gcr.io/$PROJECT_ID/$SERVICE_NAME:$PRODUCTION_TAG \
    --tag gcr.io/$PROJECT_ID/$SERVICE_NAME:latest \
    --file Dockerfile.cloudrun \
    --project $PROJECT_ID

echo "✅ Dockerイメージビルド完了"

# 4. Cloud Run本番サービスのデプロイ
echo "🚀 Cloud Run本番サービスデプロイ中..."
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME:$PRODUCTION_TAG \
    --project $PROJECT_ID \
    --region $REGION \
    --memory 512Mi \
    --cpu 1 \
    --timeout 300s \
    --max-instances 10 \
    --min-instances 0 \
    --allow-unauthenticated \
    --port 8080 \
    --set-env-vars "BUCKET_NAME=$BUCKET_NAME,APP_ENV=production" \
    --platform managed

# 5. 本番URLの取得
CLOUD_RUN_URL=$(gcloud run services describe $SERVICE_NAME \
    --region $REGION \
    --project $PROJECT_ID \
    --format="value(status.url)")

echo "✅ Cloud Run本番デプロイ完了！"
echo "🌐 Cloud Run URL: $CLOUD_RUN_URL"

# 6. 本番環境の動作確認
echo "🔍 本番環境の動作確認中..."
sleep 20

# ヘルスチェック
echo "🏥 ヘルスチェック: $CLOUD_RUN_URL/health"
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$CLOUD_RUN_URL/health" || echo "000")

if [ "$HEALTH_STATUS" = "200" ]; then
    echo "✅ ヘルスチェック成功"
else
    echo "❌ ヘルスチェック失敗 (HTTP $HEALTH_STATUS)"
    echo "⚠️ 移行を中断します"
    exit 1
fi

# 機能テスト
echo "🧪 機能テスト中..."
MAIN_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$CLOUD_RUN_URL/" || echo "000")
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$CLOUD_RUN_URL/api/status" || echo "000")

echo "メインページ: HTTP $MAIN_STATUS"
echo "APIステータス: HTTP $API_STATUS"

# 7. 移行完了の確認
if [ "$HEALTH_STATUS" = "200" ] && [ "$MAIN_STATUS" = "200" ]; then
    echo "🎉 移行完了！"
    echo ""
    echo "📊 移行結果:"
    echo "✅ Cloud Run本番環境: $CLOUD_RUN_URL"
    echo "✅ ヘルスチェック: 成功"
    echo "✅ メインページ: 成功"
    echo ""
    echo "📋 次のステップ:"
    echo "1. Railwayサービスの停止"
    echo "2. DNS設定の更新（必要に応じて）"
    echo "3. 監視の設定"
    echo "4. 古い設定ファイルの削除"
else
    echo "❌ 移行失敗"
    echo "Railway環境は引き続き稼働中です"
    exit 1
fi 