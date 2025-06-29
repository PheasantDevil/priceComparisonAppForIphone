#!/bin/bash

# App Engine APIを有効化するスクリプト
# このスクリプトは手動で実行してください

set -e

echo "🚀 App Engine APIを有効化中..."

# プロジェクトIDを確認
PROJECT_ID=$(gcloud config get-value project)
echo "プロジェクトID: $PROJECT_ID"

# App Engine APIを有効化
echo "App Engine APIを有効化しています..."
gcloud services enable appengine.googleapis.com

# 有効化されたAPIを確認
echo "有効化されたAPI:"
gcloud services list --enabled --filter="name:appengine"

echo "✅ App Engine APIの有効化が完了しました！"
echo "これでGitHub Actionsでのデプロイが可能になります。" 