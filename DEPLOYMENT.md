# デプロイメントガイド

## 概要

このアプリケーションは Render.com を使用してデプロイされます。新しいデプロイ戦略では、Dockerfile を使わずにシンプルな Python ランタイムを使用します。

## デプロイ戦略

### 1. 本番環境 (main ブランチ)

- **自動デプロイ**: main ブランチへのプッシュ時に自動デプロイ
- **設定ファイル**: `render.yaml`
- **サービス名**: `price-comparison-app`

### 2. 開発環境 (develop ブランチ)

- **自動デプロイ**: develop ブランチへのプッシュ時に自動デプロイ
- **設定ファイル**: `render-dev.yaml`
- **サービス名**: `price-comparison-app-dev`

## 必要な環境変数

### Render.com で設定が必要な環境変数

#### 必須

- `AWS_ACCESS_KEY_ID`: AWS アクセスキー
- `AWS_SECRET_ACCESS_KEY`: AWS シークレットキー
- `GOOGLE_APPLICATION_CREDENTIALS`: GCP 認証情報の JSON ファイル内容

#### オプション

- `LINE_CHANNEL_ACCESS_TOKEN`: LINE 通知用トークン
- `LINE_CHANNEL_SECRET`: LINE 通知用シークレット

## GitHub Secrets 設定

### 必要な Secrets

- `RENDER_API_KEY`: Render.com の API キー
- `RENDER_SERVICE_ID`: 本番環境のサービス ID

### Secrets の取得方法

1. **RENDER_API_KEY**

   - Render.com のダッシュボード → Account → API Keys
   - 新しい API キーを生成

2. **RENDER_SERVICE_ID**
   - Render.com のダッシュボード → Services
   - 本番環境のサービスを選択
   - URL からサービス ID を取得: `https://dashboard.render.com/web/srv-XXXXXXXXXXXX`

## デプロイフロー

### 通常の開発フロー

1. `feature/`ブランチで開発
2. `develop`ブランチにマージ → 開発環境に自動デプロイ
3. テスト完了後、`main`ブランチにマージ → 本番環境に自動デプロイ

### 緊急デプロイ

1. `main`ブランチに直接プッシュ
2. GitHub Actions が自動的に Render.com にデプロイをトリガー

## トラブルシューティング

### よくある問題

1. **Playwright のインストールエラー**

   - 解決策: `buildCommand`で`playwright install chromium`を実行

2. **GCP 認証エラー**

   - 解決策: 環境変数`GOOGLE_APPLICATION_CREDENTIALS`を正しく設定

3. **メモリ不足エラー**
   - 解決策: `startCommand`のワーカー数を 1 に減らす

### ログの確認方法

- Render.com のダッシュボード → Services → 該当サービス → Logs

## ローカル開発

### 環境構築

```bash
# 依存関係のインストール
pip install -r requirements.txt

# Playwrightのインストール
playwright install chromium

# アプリケーションの起動
python app.py
```

### 環境変数の設定

`.env`ファイルを作成して必要な環境変数を設定してください。
