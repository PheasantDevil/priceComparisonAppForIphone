# Railway 環境変数設定ガイド

## 🚀 Railway.app での必須環境変数

### 1. Railway ダッシュボードでの設定

1. [Railway.app](https://railway.app/) にアクセス
2. プロジェクト `price-comparison-app` を選択
3. **"Variables"** タブをクリック
4. 以下の環境変数を追加：

### 2. 必須環境変数

```bash
# アプリケーション設定
APP_ENV=production
SECRET_KEY=3C2jgeNUv6cfkksXVxiDuw1nI1WvCRxZYpUzeAZzsIIQ2uXh7UCSoTXYwNlRmThrdNRqN6cd0x4VYAQ-mF7lAg

# ストレージ設定（オプション）
BUCKET_NAME=price-comparison-app-data

# Google Cloud Storage（オプション）
GOOGLE_APPLICATION_CREDENTIALS_JSON={"type":"service_account","project_id":"your-project-id",...}
```

### 3. 環境変数設定手順

#### 3.1 基本設定

1. **"New Variable"** をクリック
2. **Key**: `APP_ENV`
3. **Value**: `production`
4. **"Add Variable"** をクリック

#### 3.2 セキュリティキー

1. **"New Variable"** をクリック
2. **Key**: `SECRET_KEY`
3. **Value**: `3C2jgeNUv6cfkksXVxiDuw1nI1WvCRxZYpUzeAZzsIIQ2uXh7UCSoTXYwNlRmThrdNRqN6cd0x4VYAQ-mF7lAg`
4. **"Add Variable"** をクリック

#### 3.3 ストレージ設定（オプション）

1. **"New Variable"** をクリック
2. **Key**: `BUCKET_NAME`
3. **Value**: `price-comparison-app-data`
4. **"Add Variable"** をクリック

### 4. GitHub Secrets 設定

#### 4.1 Railway Token の取得

1. Railway ダッシュボードで **"Settings"** タブをクリック
2. **"Tokens"** セクションで **"Generate Token"** をクリック
3. **Token Name**: `github-actions-deploy`
4. **"Generate Token"** をクリック
5. 生成されたトークンをコピー

#### 4.2 GitHub Secrets の設定

1. GitHub リポジトリ `priceComparisonAppForIphone` にアクセス
2. **"Settings"** タブをクリック
3. **"Secrets and variables"** → **"Actions"** をクリック
4. **"New repository secret"** をクリック
5. **Name**: `RAILWAY_TOKEN`
6. **Value**: Railway で生成したトークン
7. **"Add secret"** をクリック

### 5. 動作確認

#### 5.1 デプロイ確認

1. main ブランチにプッシュ
2. GitHub Actions でデプロイ状況を確認
3. Railway ダッシュボードでデプロイ状況を確認

#### 5.2 ヘルスチェック

```bash
curl https://your-app-url.railway.app/health
```

期待される応答:

```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00.000000",
  "storage_available": true,
  "app": "Price Comparison App",
  "version": "1.0.0",
  "environment": "production"
}
```

### 6. トラブルシューティング

#### 6.1 よくある問題

**デプロイ失敗**

- Railway ダッシュボードのログを確認
- 環境変数が正しく設定されているか確認

**アプリが起動しない**

- Railway ダッシュボードで **"Logs"** タブを確認
- ポート設定を確認（Railway は自動で `$PORT` を設定）

**環境変数エラー**

- 値に特殊文字が含まれていないか確認
- キー名が正しいか確認

### 7. 完了チェックリスト

- [ ] Railway プロジェクト作成
- [ ] 環境変数設定完了
- [ ] Railway Token 取得
- [ ] GitHub Secrets 設定
- [ ] 初回デプロイ成功
- [ ] ヘルスチェック成功
- [ ] アプリケーション動作確認
