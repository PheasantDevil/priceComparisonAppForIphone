# Google Cloud Platform (GCP) App Engine Standard デプロイメントガイド

## 概要

このアプリケーションを Google Cloud Platform の App Engine Standard でデプロイする方法を説明します。App Engine Standard は無料枠が使いやすく、コスト効率の良いプラットフォームです。

## 前提条件

1. **Google Cloud SDK** がインストールされている
2. **Google Cloud プロジェクト** が作成されている
3. **必要な API** が有効化されている

## 必要な API の有効化

```bash
# App Engine API
gcloud services enable appengine.googleapis.com

# Cloud Storage API
gcloud services enable storage.googleapis.com

# Secret Manager API
gcloud services enable secretmanager.googleapis.com
```

## デプロイ手順

### 1. プロジェクトの設定

```bash
# プロジェクトIDを設定
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID
```

### 2. サービスアカウントの作成

```bash
# サービスアカウントを作成
gcloud iam service-accounts create price-comparison-app \
    --display-name="Price Comparison App Service Account"

# 必要な権限を付与
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:price-comparison-app@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:price-comparison-app@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

### 3. サービスアカウントキーの作成

```bash
# キーを作成
gcloud iam service-accounts keys create key.json \
    --iam-account=price-comparison-app@$PROJECT_ID.iam.gserviceaccount.com
```

### 4. Secret Manager に認証情報を保存

```bash
# Secret Managerに認証情報を保存
echo "$(cat key.json)" | gcloud secrets create gcp-credentials \
    --data-file=- \
    --replication-policy="automatic"
```

### 5. Cloud Storage バケットの作成

```bash
# バケットを作成
gsutil mb gs://price-comparison-app-data-$PROJECT_ID

# バケット名を環境変数に設定
export BUCKET_NAME="price-comparison-app-data-$PROJECT_ID"
```

### 6. App Engine アプリケーションの作成

```bash
# App Engineアプリケーションを作成
gcloud app create --region=us-central
```

### 7. App Engine Standard にデプロイ

```bash
# App Engineにデプロイ
gcloud app deploy app.yaml --quiet
```

## デプロイ後の確認

### 1. サービス URL の取得

```bash
# サービスURLを取得
gcloud app browse --no-launch-browser
```

### 2. ヘルスチェック

```bash
# ヘルスチェック
curl https://your-app-id.uc.r.appspot.com/health
```

### 3. アプリケーションの動作確認

```bash
# メインページ
curl https://your-app-id.uc.r.appspot.com/

# 価格データ取得
curl https://your-app-id.uc.r.appspot.com/get_prices
```

## 自動デプロイの設定

### GitHub Actions を使用した自動デプロイ

```yaml
# .github/workflows/deploy-to-app-engine.yml
name: Deploy to App Engine Standard

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Deploy to App Engine
        run: gcloud app deploy app.yaml --quiet
```

## コスト最適化

### 1. リソース設定

```yaml
# app.yaml
resources:
  cpu: 0.5
  memory_gb: 0.25
  disk_size_gb: 1
```

### 2. スケーリング設定

```yaml
# app.yaml
automatic_scaling:
  target_cpu_utilization: 0.6
  min_instances: 0
  max_instances: 1
```

## 監視とログ

### 1. ログの確認

```bash
# リアルタイムログ
gcloud app logs tail -s default
```

### 2. メトリクスの確認

```bash
# App Engineメトリクス
gcloud app instances list
```

## トラブルシューティング

### よくある問題

1. **認証エラー**

   ```bash
   # サービスアカウントの権限を確認
   gcloud projects get-iam-policy $PROJECT_ID
   ```

2. **メモリ不足**

   ```yaml
   # app.yamlでメモリを増やす
   resources:
     memory_gb: 0.5
   ```

3. **タイムアウトエラー**
   ```yaml
   # app.yamlでタイムアウトを延長
   entrypoint: gunicorn -b :$PORT app:app --timeout 300
   ```

## セキュリティ

1. **HTTPS 強制**

   - App Engine は自動的に HTTPS を提供

2. **認証**

   - 必要に応じて IAM 認証を有効化

3. **シークレット管理**
   - Secret Manager を使用して認証情報を安全に管理

## コスト見積もり

App Engine Standard の料金（米国リージョン）：

- **無料枠**: 月 28 時間
- **追加料金**: $0.05/時間
- **リクエスト**: 無料

月間使用例：

- **軽量使用**: $0（無料枠内）
- **中程度使用**: $1-5/月
- **本格運用**: $10-20/月

## アプリケーションの動作確認

デプロイ完了後、以下のエンドポイントで動作確認：

1. **ヘルスチェック**: `https://your-app-id.uc.r.appspot.com/health`
2. **メインページ**: `https://your-app-id.uc.r.appspot.com/`
3. **価格データ取得**: `https://your-app-id.uc.r.appspot.com/get_prices`
4. **スクレイピング実行**: `https://your-app-id.uc.r.appspot.com/scrape-prices` (POST)
