# Vercel + GCP 移行ガイド

このドキュメントは、Railway から Vercel + GCP（Cloud Run）への移行手順を説明します。

## 🎯 移行の目的

- **安定性の向上**: Cloud Run の自動スケーリングと高可用性
- **コスト最適化**: 無料枠の活用と予測可能な料金体系
- **パフォーマンス向上**: Vercel の高速 CDN と Cloud Run の低レイテンシー
- **開発体験の改善**: モダンな CI/CD パイプライン

## 🏗️ 新しいアーキテクチャ

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Database      │
│   (Vercel)      │◄──►│   (Cloud Run)   │◄──►│   (Firestore)   │
│   Next.js       │    │   Flask         │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CDN           │    │   Auto Scaling  │    │   Cloud Storage │
│   Global Edge   │    │   0-10 instances│    │   File Storage  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📋 移行前の準備

### 1. 必要なアカウント

- [Google Cloud Platform](https://cloud.google.com/) アカウント
- [Vercel](https://vercel.com/) アカウント
- GitHub アカウント

### 2. 必要なツール

```bash
# Google Cloud CLI
curl https://sdk.cloud.google.com | bash
gcloud init

# Vercel CLI
npm i -g vercel

# Docker
# https://docs.docker.com/get-docker/
```

## 🚀 移行手順

### Phase 1: GCP プロジェクトのセットアップ

```bash
# 1. プロジェクトの作成
gcloud projects create price-comparison-app-123456

# 2. プロジェクトの設定
gcloud config set project price-comparison-app-123456

# 3. 必要なAPIの有効化
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable storage.googleapis.com

# 4. サービスアカウントの作成
gcloud iam service-accounts create price-comparison-app \
  --display-name="Price Comparison App Service Account"

# 5. 権限の付与
gcloud projects add-iam-policy-binding price-comparison-app-123456 \
  --member="serviceAccount:price-comparison-app@price-comparison-app-123456.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding price-comparison-app-123456 \
  --member="serviceAccount:price-comparison-app@price-comparison-app-123456.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

# 6. サービスアカウントキーの作成
gcloud iam service-accounts keys create gcp-key.json \
  --iam-account=price-comparison-app@price-comparison-app-123456.iam.gserviceaccount.com
```

### Phase 2: Vercel プロジェクトのセットアップ

```bash
# 1. Vercel CLIでログイン
vercel login

# 2. プロジェクトの初期化
cd frontend
vercel

# 3. 環境変数の設定
vercel env add BACKEND_URL
# 値: https://price-comparison-app-asia-northeast1.run.app
```

### Phase 3: GitHub Secrets の設定

GitHub リポジトリの Settings > Secrets and variables > Actions で以下を設定：

1. **GCP_SA_KEY**: `gcp-key.json` の内容
2. **GOOGLE_APPLICATION_CREDENTIALS_JSON**: サービスアカウントキーの JSON 文字列
3. **VERCEL_TOKEN**: Vercel API Token
4. **VERCEL_ORG_ID**: Vercel Organization ID
5. **VERCEL_PROJECT_ID**: Vercel Project ID

### Phase 4: 初回デプロイ

```bash
# 1. ブランチの作成
git checkout -b feature/vercel-gcp-migration

# 2. 変更のコミット
git add .
git commit -m "Migrate to Vercel + GCP architecture"

# 3. プッシュとプルリクエスト作成
git push origin feature/vercel-gcp-migration
```

## 🔧 設定ファイルの説明

### vercel.json

```json
{
  "version": 2,
  "builds": [
    {
      "src": "frontend/package.json",
      "use": "@vercel/next"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "https://price-comparison-app-asia-northeast1.run.app/api/$1"
    }
  ]
}
```

### Dockerfile.cloudrun

```dockerfile
# マルチステージビルド
FROM node:18-alpine AS frontend-builder
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install -r requirements.txt
COPY backend/ ./
COPY --from=frontend-builder /app/out ./templates
EXPOSE 8080
CMD ["python", "app.py"]
```

## 📊 パフォーマンス比較

| 項目         | Railway     | Vercel + Cloud Run                 |
| ------------ | ----------- | ---------------------------------- |
| 無料枠       | 月 500 時間 | 月 200 万リクエスト + 100GB 帯域幅 |
| スケーリング | 手動        | 自動 (0-10 インスタンス)           |
| レイテンシー | 中          | 低 (エッジ配信)                    |
| 可用性       | 99.5%       | 99.9%                              |
| 料金予測性   | 低          | 高                                 |

## 🔍 移行後の検証

### 1. ヘルスチェック

```bash
# Cloud Run
curl https://price-comparison-app-asia-northeast1.run.app/health

# Vercel
curl https://your-app.vercel.app/health
```

### 2. パフォーマンステスト

```bash
# ロードテスト
ab -n 1000 -c 10 https://your-app.vercel.app/
```

### 3. ログの確認

```bash
# Cloud Run ログ
gcloud logging read "resource.type=cloud_run_revision" --limit=50

# Vercel ログ
vercel logs
```

## 🚨 トラブルシューティング

### よくある問題

1. **CORS エラー**

   ```python
   # backend/app.py
   from flask_cors import CORS
   CORS(app, origins=["*"])
   ```

2. **環境変数の問題**

   ```bash
   # Cloud Run で環境変数を確認
   gcloud run services describe price-comparison-app \
     --region=asia-northeast1 \
     --format="value(spec.template.spec.containers[0].env[].name)"
   ```

3. **ビルドエラー**
   ```bash
   # ローカルでビルドテスト
   docker build -f Dockerfile.cloudrun -t test-image .
   ```

## 📈 監視とアラート

### Cloud Monitoring の設定

```bash
# アラートポリシーの作成
gcloud alpha monitoring policies create \
  --policy-from-file=monitoring-policy.yaml
```

### ログ分析

```bash
# エラーログの確認
gcloud logging read "severity>=ERROR" --limit=100
```

## 🔄 ロールバック手順

### Railway への復帰

```bash
# 1. Railway の再デプロイ
railway up

# 2. ドメインの切り替え
# DNS レコードを Railway の URL に変更
```

## 📝 移行チェックリスト

- [ ] GCP プロジェクトの作成
- [ ] 必要な API の有効化
- [ ] サービスアカウントの作成
- [ ] Vercel プロジェクトの設定
- [ ] GitHub Secrets の設定
- [ ] 初回デプロイの実行
- [ ] ヘルスチェックの確認
- [ ] パフォーマンステストの実行
- [ ] ログの確認
- [ ] Railway サービスの停止

## 🎉 移行完了

移行が完了したら、以下の点を確認してください：

1. **機能テスト**: すべての機能が正常に動作することを確認
2. **パフォーマンス**: レスポンス時間が改善されていることを確認
3. **コスト**: 月額料金が予想範囲内であることを確認
4. **監視**: ログとメトリクスが正常に収集されていることを確認

## 📞 サポート

移行中に問題が発生した場合は、以下を確認してください：

- [Google Cloud ドキュメント](https://cloud.google.com/docs)
- [Vercel ドキュメント](https://vercel.com/docs)
- [GitHub Issues](https://github.com/yourusername/priceComparisonAppForIphone/issues)
