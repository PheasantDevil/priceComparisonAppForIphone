# Google Cloud Platform (GCP) デプロイメントガイド

## 概要

このアプリケーションを Google Cloud Platform でデプロイする方法を説明します。Cloud Run を使用することで、サーバーレスでスケーラブルなデプロイが可能です。

## 前提条件

1. **Google Cloud SDK** がインストールされている
2. **Google Cloud プロジェクト** が作成されている
3. **必要な API** が有効化されている

## 必要な API の有効化

```bash
# Cloud Run API
gcloud services enable run.googleapis.com

# Container Registry API
gcloud services enable containerregistry.googleapis.com

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

### 6. Docker イメージのビルドとプッシュ

```bash
# Dockerイメージをビルド
docker build -t gcr.io/$PROJECT_ID/price-comparison-app .

# Container Registryにプッシュ
docker push gcr.io/$PROJECT_ID/price-comparison-app
```

### 7. Cloud Run にデプロイ

```bash
# Cloud Runにデプロイ
gcloud run deploy price-comparison-app \
    --image gcr.io/$PROJECT_ID/price-comparison-app \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --service-account=price-comparison-app@$PROJECT_ID.iam.gserviceaccount.com \
    --set-secrets=GOOGLE_APPLICATION_CREDENTIALS_JSON=gcp-credentials:latest \
    --set-env-vars=BUCKET_NAME=$BUCKET_NAME,APP_ENV=production \
    --memory 512Mi \
    --cpu 1 \
    --timeout 300 \
    --concurrency 80 \
    --max-instances 10
```

## デプロイ後の確認

### 1. サービス URL の取得

```bash
# サービスURLを取得
gcloud run services describe price-comparison-app \
    --platform managed \
    --region us-central1 \
    --format="value(status.url)"
```

### 2. ヘルスチェック

```bash
# ヘルスチェック
curl https://your-service-url/health
```

### 3. アプリケーションの動作確認

```bash
# メインページ
curl https://your-service-url/

# 価格データ取得
curl https://your-service-url/get_prices
```

## 自動デプロイの設定

### GitHub Actions を使用した自動デプロイ

```yaml
# .github/workflows/deploy.yml
name: Deploy to Cloud Run

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v2
        with:
          project_id: ${{ secrets.GCP_PROJECT_ID }}
          service_account_key: ${{ secrets.GCP_SA_KEY }}

      - name: Build and push Docker image
        run: |
          docker build -t gcr.io/${{ secrets.GCP_PROJECT_ID }}/price-comparison-app .
          docker push gcr.io/${{ secrets.GCP_PROJECT_ID }}/price-comparison-app

      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy price-comparison-app \
            --image gcr.io/${{ secrets.GCP_PROJECT_ID }}/price-comparison-app \
            --platform managed \
            --region us-central1 \
            --allow-unauthenticated
```

## コスト最適化

### 1. スケーリング設定

```bash
# 最小インスタンス数を0に設定（コスト削減）
gcloud run services update price-comparison-app \
    --region us-central1 \
    --min-instances 0 \
    --max-instances 5
```

### 2. リソース制限

```bash
# メモリとCPUを最適化
gcloud run services update price-comparison-app \
    --region us-central1 \
    --memory 256Mi \
    --cpu 0.5
```

## 監視とログ

### 1. ログの確認

```bash
# リアルタイムログ
gcloud logs tail --service=price-comparison-app
```

### 2. メトリクスの確認

```bash
# Cloud Runメトリクス
gcloud run services describe price-comparison-app \
    --region us-central1 \
    --format="value(status.conditions)"
```

## トラブルシューティング

### よくある問題

1. **認証エラー**

   ```bash
   # サービスアカウントの権限を確認
   gcloud projects get-iam-policy $PROJECT_ID
   ```

2. **メモリ不足**

   ```bash
   # メモリを増やす
   gcloud run services update price-comparison-app \
       --region us-central1 \
       --memory 1Gi
   ```

3. **タイムアウトエラー**
   ```bash
   # タイムアウトを延長
   gcloud run services update price-comparison-app \
       --region us-central1 \
       --timeout 600
   ```

## セキュリティ

1. **HTTPS 強制**

   - Cloud Run は自動的に HTTPS を提供

2. **認証**

   - 必要に応じて IAM 認証を有効化

3. **シークレット管理**
   - Secret Manager を使用して認証情報を安全に管理

## コスト見積もり

Cloud Run の料金（米国リージョン）：

- **CPU**: $0.00002400/秒
- **メモリ**: $0.00000250/秒/GB
- **リクエスト**: $0.40/100 万リクエスト

月間 100 万リクエスト、平均実行時間 30 秒の場合：

- **約$5-10/月**程度
