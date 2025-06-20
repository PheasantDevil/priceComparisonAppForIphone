# Railway.app 詳細セットアップガイド

## 🎯 目標

App Engine Standard の内部エラーを回避し、安定した無料デプロイ環境を構築

## 📋 前提条件

- GitHub アカウント
- クレジットカード（Railway.app の認証用、課金なし）

## 🚀 Step-by-Step セットアップ

### **Step 1: Railway.app アカウント作成**

#### 1.1 Railway.app にアクセス

1. [Railway.app](https://railway.app/)を開く
2. **"Start a New Project"**をクリック

#### 1.2 GitHub 連携

1. **"Deploy from GitHub repo"**を選択
2. GitHub アカウントでログイン
3. リポジトリ`priceComparisonAppForIphone`を選択
4. **"Deploy Now"**をクリック

#### 1.3 プロジェクト設定

- **プロジェクト名**: `price-comparison-app`
- **サービス名**: `web`（自動設定）
- **ブランチ**: `main`

### **Step 2: 環境変数設定**

#### 2.1 Railway ダッシュボードで環境変数を設定

1. Railway プロジェクトダッシュボードにアクセス
2. **"Variables"**タブをクリック
3. 以下の環境変数を追加：

```bash
# 必須環境変数
BUCKET_NAME=price-comparison-app-data
APP_ENV=production
SECRET_KEY=your-super-secret-key-2024-railway

# オプション（Google Cloud Storage使用時）
GOOGLE_APPLICATION_CREDENTIALS_JSON={"type":"service_account","project_id":"your-project-id",...}
```

#### 2.2 環境変数設定手順

1. **"New Variable"**をクリック
2. **Key**: `BUCKET_NAME`
3. **Value**: `price-comparison-app-data`
4. **"Add Variable"**をクリック
5. 同様に他の環境変数も追加

### **Step 3: Railway Token 取得**

#### 3.1 Token 生成

1. Railway ダッシュボードで**"Settings"**タブをクリック
2. **"Tokens"**セクションで**"Generate Token"**をクリック
3. **Token Name**: `github-actions-deploy`
4. **"Generate Token"**をクリック
5. 生成されたトークンをコピー（例: `railway_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`）

### **Step 4: GitHub Secrets 設定**

#### 4.1 GitHub リポジトリ設定

1. GitHub リポジトリ`priceComparisonAppForIphone`にアクセス
2. **"Settings"**タブをクリック
3. **"Secrets and variables"** → **"Actions"**をクリック

#### 4.2 Secrets 追加

以下の 2 つのシークレットを追加：

**RAILWAY_TOKEN**

- **Name**: `RAILWAY_TOKEN`
- **Value**: Step 3 で取得したトークン

**RAILWAY_SERVICE_NAME**

- **Name**: `RAILWAY_SERVICE_NAME`
- **Value**: `web`（Railway で自動設定されたサービス名）

### **Step 5: 初回デプロイ**

#### 5.1 自動デプロイ

1. main ブランチにプッシュすると自動デプロイ開始
2. GitHub Actions でデプロイ状況を確認
3. Railway ダッシュボードでデプロイ状況を確認

#### 5.2 デプロイ確認

1. Railway ダッシュボードで**"Deployments"**タブを確認
2. デプロイが成功したら**"View"**をクリック
3. アプリケーション URL を確認（例: `https://price-comparison-app-production-xxxx.up.railway.app`）

### **Step 6: 動作確認**

#### 6.1 ヘルスチェック

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
  "version": "1.0.0"
}
```

#### 6.2 メインページ確認

ブラウザでアプリケーション URL にアクセスして動作確認

### **Step 7: トラブルシューティング**

#### 7.1 よくある問題と解決策

**デプロイ失敗**

```bash
# Railway CLIでログ確認
railway logs --service web
```

**環境変数エラー**

1. Railway ダッシュボードで環境変数を再確認
2. 値に特殊文字が含まれていないか確認

**アプリが起動しない**

1. Railway ダッシュボードで**"Logs"**タブを確認
2. ポート設定を確認（Railway は自動で`$PORT`を設定）

#### 7.2 ログ確認方法

1. Railway ダッシュボードで**"Logs"**タブをクリック
2. リアルタイムログを確認
3. エラーメッセージを確認

### **Step 8: 移行完了後のクリーンアップ**

#### 8.1 App Engine 関連ファイルの削除

Railway.app での動作確認後、以下のファイルを削除可能：

```bash
# 削除可能なファイル
app.yaml
.gcloudignore
deploy-app-engine.sh
GCP_DEPLOYMENT.md
.github/workflows/deploy-to-app-engine.yml
```

#### 8.2 削除手順

1. 動作確認完了後
2. 不要ファイルを削除
3. 変更をコミット・プッシュ

## 📊 コスト比較

| サービス            | 無料枠      | 安定性               | デプロイ難易度 |
| ------------------- | ----------- | -------------------- | -------------- |
| App Engine Standard | 月 1GB 時間 | 低（内部エラー多発） | 中             |
| Railway.app         | 月 500 時間 | 高                   | 低             |

## ✅ 完了チェックリスト

- [ ] Railway.app アカウント作成
- [ ] GitHub リポジトリ連携
- [ ] 環境変数設定
- [ ] Railway Token 取得
- [ ] GitHub Secrets 設定
- [ ] 初回デプロイ成功
- [ ] 動作確認完了
- [ ] ヘルスチェック成功

## 🆘 サポート

問題が発生した場合：

1. Railway ダッシュボードのログを確認
2. GitHub Actions のログを確認
3. 環境変数の設定を再確認
4. 必要に応じて Railway サポートに問い合わせ
