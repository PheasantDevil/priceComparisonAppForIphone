#!/bin/bash

# Cloud Runテストデプロイスクリプト
set -e

source .env.gcp

SERVICE_NAME="price-comparison-app-test"
TEST_TAG="test-$(date +%Y%m%d-%H%M%S)"

echo "🧪 Cloud Runテストデプロイを開始します..."

# 1. フロントエンドビルドのテスト
echo "🔨 フロントエンドビルドテスト..."
cd frontend
npm ci
npm run build
cd ..

# templatesディレクトリの確認
if [ ! -d "templates" ]; then
    mkdir -p templates
fi
cp -r frontend/out/* templates/

echo "✅ フロントエンドビルド完了"
echo "📁 Templates contents:"
ls -la templates/

# 2. Dockerイメージのビルドテスト
echo "🐳 Dockerイメージビルドテスト..."
gcloud builds submit \
    --tag gcr.io/$PROJECT_ID/$SERVICE_NAME:$TEST_TAG \
    --file Dockerfile.cloudrun \
    --project $PROJECT_ID

echo "✅ Dockerイメージビルド完了"

# 3. Cloud Runサービスのテストデプロイ
echo "🚀 Cloud Runテストデプロイ..."
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME:$TEST_TAG \
    --project $PROJECT_ID \
    --region $REGION \
    --memory 512Mi \
    --cpu 1 \
    --timeout 300s \
    --max-instances 2 \
    --min-instances 0 \
    --allow-unauthenticated \
    --port 8080 \
    --set-env-vars "BUCKET_NAME=$BUCKET_NAME,APP_ENV=test" \
    --platform managed

# 4. サービスURLの取得
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region $REGION \
    --project $PROJECT_ID \
    --format="value(status.url)")

echo "✅ テストデプロイ完了！"
echo "🌐 テストURL: $SERVICE_URL"

# 5. ヘルスチェック
echo "🔍 ヘルスチェックを実行中..."
sleep 15

echo "🏥 ヘルスチェック: $SERVICE_URL/health"
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$SERVICE_URL/health" || echo "000")

if [ "$HEALTH_STATUS" = "200" ]; then
    echo "✅ ヘルスチェック成功"
else
    echo "❌ ヘルスチェック失敗 (HTTP $HEALTH_STATUS)"
fi

# 6. 機能テスト
echo "🧪 機能テストを実行中..."

# メインページのテスト
echo "📄 メインページテスト: $SERVICE_URL/"
MAIN_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$SERVICE_URL/" || echo "000")
echo "メインページ: HTTP $MAIN_STATUS"

# APIステータスのテスト
echo "🔌 APIステータステスト: $SERVICE_URL/api/status"
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$SERVICE_URL/api/status" || echo "000")
echo "APIステータス: HTTP $API_STATUS"

# 7. ログの確認
echo "📋 ログを確認中..."
gcloud logs tail --service=$SERVICE_NAME --limit=20

echo ""
echo "🎉 テストデプロイ完了！"
echo "📊 結果:"
echo "- ヘルスチェック: $HEALTH_STATUS"
echo "- メインページ: $MAIN_STATUS"
echo "- APIステータス: $API_STATUS"
echo ""
echo "📋 次のステップ:"
echo "1. テスト結果の確認"
echo "2. 問題があれば修正"
echo "3. 本番デプロイの準備" 