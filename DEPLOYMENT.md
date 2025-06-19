# デプロイメントガイド

## 概要

このアプリケーションは Render.com を使用してデプロイされます。新しいデプロイ戦略では、Dockerfile を使わずにシンプルな Python ランタイムを使用します。

## デプロイ戦略

### 本番環境 (main ブランチ)

- **自動デプロイ**: main ブランチへのプッシュ時に自動デプロイ
- **設定ファイル**: `deploy/render.yaml`
- **サービス名**: `price-comparison-app`

## 必要な環境変数

### Render.com で設定が必要な環境変数

#### 必須

- `GOOGLE_APPLICATION_CREDENTIALS`: GCP 認証情報の JSON ファイル内容

### GCP 認証情報の取得方法

1. **Google Cloud Console にアクセス**

   - https://console.cloud.google.com/

2. **サービスアカウントの作成**

   - IAM と管理 → サービスアカウント
   - 「サービスアカウントを作成」をクリック
   - 名前: `price-comparison-app-render`
   - 説明: `Render.com deployment service account`

3. **必要な権限を付与**

   - Cloud Storage 管理者 (`roles/storage.admin`)
   - または、より制限的な権限:
     - Storage オブジェクト管理者 (`roles/storage.objectAdmin`)
     - Storage オブジェクト閲覧者 (`roles/storage.objectViewer`)

4. **キーの作成**

   - 作成したサービスアカウントをクリック
   - 「キー」タブ → 「鍵を追加」→ 「新しい鍵を作成」
   - JSON 形式を選択
   - ダウンロードされた JSON ファイルの内容をコピー

5. **Render.com で環境変数として設定**
   - キー: `GOOGLE_APPLICATION_CREDENTIALS`
   - 値: ダウンロードした JSON ファイルの内容（全体）

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
2. プルリクエストを作成してレビュー
3. `main`ブランチにマージ → 自動デプロイ

### 緊急デプロイ

1. `main`ブランチに直接プッシュ
2. GitHub Actions が自動的に Render.com にデプロイをトリガー

## トラブルシューティング

### よくある問題

1. **Playwright のインストールエラー**

   - 解決策: 動的インストール方式を採用
   - アプリケーション起動時に必要に応じてブラウザをインストール
   - `/scrape-prices`エンドポイントでスクレイピング実行時に自動インストール

2. **GCP 認証エラー**

   - 解決策: 環境変数`GOOGLE_APPLICATION_CREDENTIALS`を正しく設定
   - JSON ファイルの内容が正しくコピーされているか確認

3. **メモリ不足エラー**
   - 解決策: `startCommand`のワーカー数を 1 に減らし、`--preload`オプションを使用

### ログの確認方法

- Render.com のダッシュボード → Services → 該当サービス → Logs

## ローカル開発

### 環境構築

```bash
# 依存関係のインストール
pip install -r requirements.txt

# Playwrightのインストール
pip install playwright
playwright install chromium

# アプリケーションの起動
python app.py
```

### 環境変数の設定

`.env`ファイルを作成して必要な環境変数を設定してください。

## 価格スクレイピング

### スクレイピングの実行

価格スクレイピングは以下のエンドポイントで実行できます：

```bash
curl -X POST https://your-app.onrender.com/scrape-prices
```

このエンドポイントは：

1. Playwright ブラウザの存在をチェック
2. 必要に応じてブラウザをインストール
3. 価格スクレイピングを実行
4. 結果を Cloud Storage に保存

### 自動スクレイピング

GitHub Actions を使用して定期的にスクレイピングを実行する場合は、`.github/workflows/scrape_prices.yml`を参照してください。
