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

#### 4.2 Project ID と Service ID の取得

1. Railway ダッシュボードでプロジェクトを選択
2. **"Settings"** タブをクリック
3. **Project ID** をコピー（例: `4f0bf6cf-f794-41a9-9c8c-1f74bc38ab48`）
4. サービスページで **Service ID** をコピー（例: `9b4de8d6-2fab-4cc6-80a2-3d742b566990`）

#### 4.3 GitHub Secrets の設定

1. GitHub リポジトリ `priceComparisonAppForIphone` にアクセス
2. **"Settings"** タブをクリック
3. **"Secrets and variables"** → **"Actions"** をクリック
4. 以下の 3 つのシークレットを追加：

**RAILWAY_TOKEN**

- **Name**: `RAILWAY_TOKEN`
- **Value**: Railway で生成したトークン

**RAILWAY_PROJECT_ID**

- **Name**: `RAILWAY_PROJECT_ID`
- **Value**: Railway プロジェクトの ID（例: `4f0bf6cf-f794-41a9-9c8c-1f74bc38ab48`）

**RAILWAY_SERVICE_ID**

- **Name**: `RAILWAY_SERVICE_ID`
- **Value**: Railway サービスの ID（例: `9b4de8d6-2fab-4cc6-80a2-3d742b566990`）

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
- Project ID と Service ID が正しいか確認

**アプリが起動しない**

- Railway ダッシュボードで **"Logs"** タブを確認
- ポート設定を確認（Railway は自動で `$PORT` を設定）

**環境変数エラー**

- 値に特殊文字が含まれていないか確認
- キー名が正しいか確認

**Project ID または Service ID エラー**

- Railway ダッシュボードで正しい ID を確認
- GitHub Secrets に正しく設定されているか確認

### 7. 完了チェックリスト

- [ ] Railway プロジェクト作成
- [ ] 環境変数設定完了
- [ ] Railway Token 取得
- [ ] Project ID 取得
- [ ] Service ID 取得
- [ ] GitHub Secrets 設定（3 つすべて）
- [ ] 初回デプロイ成功
- [ ] ヘルスチェック成功
- [ ] アプリケーション動作確認
