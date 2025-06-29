# Railway.app デプロイガイド

## 概要

App Engine Standard の内部エラーを回避するため、Railway.app に移行します。

## Railway.app の利点

- ✅ **完全無料**: 月 500 時間まで無料
- ✅ **安定性**: App Engine Standard より安定
- ✅ **簡単デプロイ**: GitHub 連携で自動デプロイ
- ✅ **柔軟性**: カスタム環境変数設定可能

## セットアップ手順

### 1. Railway.app アカウント作成

1. [Railway.app](https://railway.app/)にアクセス
2. GitHub アカウントでログイン
3. 新しいプロジェクトを作成

### 2. GitHub Secrets 設定

以下の Secrets を GitHub リポジトリに設定：

#### `RAILWAY_TOKEN`

- Railway.app のアクセストークン
- Railway.app の設定画面から取得

#### `RAILWAY_SERVICE_NAME`

- Railway プロジェクト内のサービス名
- 通常は `price-comparison-app` など

### 3. 環境変数設定

Railway.app のダッシュボードで以下を設定：

```
BUCKET_NAME=price-comparison-app-data
APP_ENV=production
SECRET_KEY=your-secret-key-here
```

### 4. デプロイ

main ブランチにプッシュすると自動デプロイされます。

## デプロイ確認

デプロイ後、以下の URL でアクセス可能：

```
https://your-app-name.railway.app
```

## トラブルシューティング

### よくある問題

1. **デプロイ失敗**

   - Railway CLI のバージョンを確認
   - 環境変数が正しく設定されているか確認

2. **アプリが起動しない**

   - ログを確認
   - ポート設定を確認（Railway は自動で`$PORT`を設定）

3. **環境変数エラー**
   - Railway ダッシュボードで環境変数を再設定

## コスト

- **無料枠**: 月 500 時間まで無料
- **追加料金**: 500 時間を超える場合のみ課金

## 移行完了後

App Engine Standard の設定ファイルは削除可能：

- `app.yaml`
- `.gcloudignore`
- App Engine 関連のスクリプト
