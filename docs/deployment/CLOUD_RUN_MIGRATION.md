# Railway から Cloud Run への移行ガイド

## 概要

Railway から Google Cloud Run への移行により、より安定した運用とコスト効率の向上を実現します。

## 移行のメリット

### 🆓 **無料枠の比較**

| プラットフォーム | 無料枠              | 制限             |
| ---------------- | ------------------- | ---------------- |
| Railway          | 月 500 時間         | 時間ベース       |
| Cloud Run        | 月 200 万リクエスト | リクエストベース |

### 🚀 **安定性の向上**

- **Google のインフラ**: 99.9%の可用性保証
- **自動スケーリング**: 0〜1000 インスタンスまで自動調整
- **グローバル CDN**: 高速なコンテンツ配信

### 💰 **コスト効率**

- **予測可能な料金**: リクエストベースの課金
- **使用しない時間は課金なし**: コールドスタート対応
- **無料枠が充実**: 小〜中規模アプリに最適

## 移行手順

### 1. 前提条件

```bash
# Google Cloud SDK のインストール
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init

# プロジェクトの設定
gcloud config set project price-comparison-app-463007
```

### 2. 必要な API の有効化

```bash
gcloud services enable run.googleapis.com \
    storage.googleapis.com \
    secretmanager.googleapis.com \
    cloudbuild.googleapis.com
```

### 3. サービスアカウントの設定

```bash
# サービスアカウントの作成（既存のものを使用）
gcloud iam service-accounts create price-comparison-app \
    --display-name="Price Comparison App Service Account"

# 必要な権限を付与
gcloud projects add-iam-policy-binding price-comparison-app-463007 \
    --member="serviceAccount:price-comparison-app@price-comparison-app-463007.iam.gserviceaccount.com" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding price-comparison-app-463007 \
    --member="serviceAccount:price-comparison-app@price-comparison-app-463007.iam.gserviceaccount.com" \
    --role="roles/storage.admin"
```

### 4. GitHub Secrets の設定

以下の Secrets を GitHub リポジトリに設定：

- `GCP_SA_KEY`: サービスアカウントの JSON キー

### 5. デプロイの実行

#### 手動デプロイ

```bash
# デプロイスクリプトの実行
chmod +x infrastructure/gcp/deploy-cloud-run-main.sh
./infrastructure/gcp/deploy-cloud-run-main.sh
```

#### 自動デプロイ（GitHub Actions）

main ブランチにプッシュすると自動的にデプロイされます。

## 設定ファイルの説明

### Dockerfile.cloudrun

- マルチステージビルドでフロントエンド・バックエンドを統合
- Cloud Run 環境に最適化
- ポート 8080 で動作

### .github/workflows/deploy-to-cloud-run.yml

- GitHub Actions による自動デプロイ
- フロントエンドビルド → Docker ビルド → Cloud Run デプロイ
- ヘルスチェックと PR コメント機能

## 移行後の確認事項

### 1. アプリケーションの動作確認

```bash
# サービスURLの取得
gcloud run services describe price-comparison-app \
    --region asia-northeast1 \
    --format="value(status.url)"

# ヘルスチェック
curl https://your-service-url/health
```

### 2. ログの確認

```bash
# リアルタイムログ
gcloud logs tail --service=price-comparison-app
```

### 3. メトリクスの確認

```bash
# Cloud Run メトリクス
gcloud run services describe price-comparison-app \
    --region asia-northeast1
```

## トラブルシューティング

### よくある問題

1. **デプロイ失敗**

   - Dockerfile.cloudrun の構文エラー
   - サービスアカウントの権限不足
   - プロジェクト ID の不一致

2. **アプリケーションが起動しない**

   - ポート設定の確認（8080）
   - 環境変数の設定
   - ログの確認

3. **フロントエンドが表示されない**
   - templates ディレクトリの確認
   - ビルドプロセスの確認

## コスト最適化

### 1. リソース設定

```bash
# メモリとCPUの最適化
--memory 512Mi --cpu 1
```

### 2. スケーリング設定

```bash
# インスタンス数の制限
--max-instances 10 --min-instances 0
```

### 3. タイムアウト設定

```bash
# リクエストタイムアウト
--timeout 300s
```

## Railway からの移行完了後

移行が完了し、動作確認が取れたら以下を実行：

1. **Railway サービスの停止**

   - Railway ダッシュボードでサービスを停止
   - 課金の停止

2. **設定ファイルの整理**

   - `railway.json` の削除
   - Railway 関連のスクリプトの削除

3. **ドキュメントの更新**
   - デプロイ手順の更新
   - README の更新

## サポート

移行中に問題が発生した場合は：

1. Cloud Run のログを確認
2. GitHub Actions のログを確認
3. サービスアカウントの権限を確認
4. プロジェクト設定を確認
