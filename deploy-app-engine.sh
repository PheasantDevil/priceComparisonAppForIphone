#!/bin/bash

# App Engine Standard デプロイスクリプト
set -e

# 環境変数の設定
export PROJECT_ID="your-project-id"  # 実際のプロジェクトIDに変更

echo "🚀 App Engine Standard にデプロイを開始します..."

# 1. プロジェクトの設定
echo "⚙️ プロジェクトを設定中..."
gcloud config set project $PROJECT_ID

# 2. App Engine APIの有効化
echo "📋 App Engine APIを有効化中..."
gcloud services enable appengine.googleapis.com storage.googleapis.com secretmanager.googleapis.com

# 3. サービスアカウントの作成（存在しない場合）
echo "👤 サービスアカウントを確認中..."
if ! gcloud iam service-accounts describe price-comparison-app@$PROJECT_ID.iam.gserviceaccount.com > /dev/null 2>&1; then
    echo "サービスアカウントを作成中..."
    gcloud iam service-accounts create price-comparison-app \
        --display-name="Price Comparison App Service Account"
    
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:price-comparison-app@$PROJECT_ID.iam.gserviceaccount.com" \
        --role="roles/storage.admin"
    
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:price-comparison-app@$PROJECT_ID.iam.gserviceaccount.com" \
        --role="roles/secretmanager.secretAccessor"
fi

# 4. サービスアカウントキーの作成
echo "🔑 サービスアカウントキーを作成中..."
gcloud iam service-accounts keys create key.json \
    --iam-account=price-comparison-app@$PROJECT_ID.iam.gserviceaccount.com

# 5. Secret Managerに認証情報を保存
echo "🔐 Secret Managerに認証情報を保存中..."
echo "$(cat key.json)" | gcloud secrets create gcp-credentials \
    --data-file=- \
    --replication-policy="automatic" || echo "Secret already exists"

# 6. Cloud Storageバケットの作成
echo "📦 Cloud Storageバケットを作成中..."
gsutil mb gs://price-comparison-app-data-$PROJECT_ID || echo "Bucket already exists"

# 7. app.yamlの環境変数を置換
echo "🔧 app.yamlの環境変数を設定中..."
sed -i.bak "s/PROJECT_ID/$PROJECT_ID/g" app.yaml

# 8. App Engineアプリケーションの作成（初回のみ）
echo "📱 App Engineアプリケーションを作成中..."
gcloud app create --region=us-central || echo "App Engine app already exists"

# 9. デプロイ
echo "🚀 App Engineにデプロイ中..."
gcloud app deploy app.yaml --quiet

# 10. サービスURLの取得
echo "🔗 サービスURLを取得中..."
SERVICE_URL=$(gcloud app browse --no-launch-browser)

echo "✅ デプロイ完了！"
echo "🌐 サービスURL: $SERVICE_URL"
echo "🏥 ヘルスチェック: $SERVICE_URL/health"

# 11. クリーンアップ
echo "🧹 一時ファイルを削除中..."
rm -f key.json
mv app.yaml.bak app.yaml 2>/dev/null || true

echo "🎉 App Engine Standard へのデプロイが完了しました！" 