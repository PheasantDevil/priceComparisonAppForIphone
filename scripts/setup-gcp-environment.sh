#!/bin/bash

# GCP環境セットアップスクリプト
set -e

PROJECT_ID="price-comparison-app-463007"
REGION="asia-northeast1"
SERVICE_ACCOUNT_NAME="price-comparison-app"

echo "🚀 GCP環境のセットアップを開始します..."

# 1. プロジェクトの設定
echo "⚙️ プロジェクトを設定中..."
gcloud config set project $PROJECT_ID

# 2. 必要なAPIの有効化
echo "📋 必要なAPIを有効化中..."
gcloud services enable run.googleapis.com \
    storage.googleapis.com \
    secretmanager.googleapis.com \
    cloudbuild.googleapis.com \
    containerregistry.googleapis.com

# 3. サービスアカウントの作成
echo "👤 サービスアカウントを作成中..."
if ! gcloud iam service-accounts describe $SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com > /dev/null 2>&1; then
    gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
        --display-name="Price Comparison App Service Account"
    
    echo "✅ サービスアカウントを作成しました"
else
    echo "ℹ️ サービスアカウントは既に存在します"
fi

# 4. 必要な権限を付与
echo "🔑 権限を付与中..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/cloudbuild.builds.builder"

# 5. サービスアカウントキーの作成
echo "🔐 サービスアカウントキーを作成中..."
gcloud iam service-accounts keys create gcp-service-account-key.json \
    --iam-account=$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com

# 6. Cloud Storageバケットの確認・作成
echo "📦 Cloud Storageバケットを確認中..."
BUCKET_NAME="price-comparison-app-data"
if ! gsutil ls gs://$BUCKET_NAME > /dev/null 2>&1; then
    echo "バケットを作成中..."
    gsutil mb -l $REGION gs://$BUCKET_NAME
    echo "✅ バケットを作成しました"
else
    echo "ℹ️ バケットは既に存在します"
fi

# 7. 環境変数の設定
echo "🔧 環境変数を設定中..."
echo "PROJECT_ID=$PROJECT_ID" > .env.gcp
echo "REGION=$REGION" >> .env.gcp
echo "SERVICE_ACCOUNT_NAME=$SERVICE_ACCOUNT_NAME" >> .env.gcp
echo "BUCKET_NAME=$BUCKET_NAME" >> .env.gcp

echo "✅ GCP環境のセットアップが完了しました！"
echo ""
echo "📋 次のステップ:"
echo "1. GitHub SecretsにGCP_SA_KEYを設定"
echo "2. サービスアカウントキーを安全に保存"
echo "3. Cloud Runデプロイのテスト実行" 