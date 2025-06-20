#!/bin/bash

# App Engine権限修正スクリプト
# このスクリプトは手動で実行してください

set -e

echo "🔧 App Engine権限を修正中..."

# プロジェクトIDを確認
PROJECT_ID=$(gcloud config get-value project)
echo "プロジェクトID: $PROJECT_ID"

# サービスアカウント名
SERVICE_ACCOUNT="price-comparison-app@$PROJECT_ID.iam.gserviceaccount.com"

echo "サービスアカウント: $SERVICE_ACCOUNT"

# App Engine関連の権限を付与
echo "App Engine権限を付与中..."

# App Engine管理者権限
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/appengine.admin"

# App Engine開発者権限
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/appengine.deployer"

# App Engineビューアー権限
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/appengine.appViewer"

# App Engineサービス管理者権限
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/appengine.serviceAdmin"

# サービスアカウントユーザー権限
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/iam.serviceAccountUser"

# サービス使用量管理者権限
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/serviceusage.serviceUsageAdmin"

echo "✅ App Engine権限の修正が完了しました！"
echo "これでGitHub Actionsでのデプロイが可能になります。" 