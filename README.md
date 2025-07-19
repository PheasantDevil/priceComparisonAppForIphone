# Price Comparison App for iPhone

価格比較アプリケーション - iPhone 製品の価格を比較・追跡するための Web アプリケーション

## 🏗️ アーキテクチャ

このアプリケーションは **Vercel + GCP（Cloud Run）** のハイブリッドアーキテクチャを採用しています：

- **フロントエンド**: Vercel (Next.js 15.3.3)
- **バックエンド**: Google Cloud Run (Flask)
- **データベース**: Firestore
- **ストレージ**: Cloud Storage
- **CI/CD**: GitHub Actions

## 🚀 デプロイメント

### フロントエンド (Vercel)

フロントエンドは Vercel に自動デプロイされます：

```bash
# 手動デプロイ（必要な場合）
cd frontend
vercel --prod
```

### バックエンド (Cloud Run)

バックエンドは GitHub Actions で自動デプロイされます：

```bash
# 手動デプロイ（必要な場合）
gcloud run deploy price-comparison-app \
  --source . \
  --platform managed \
  --region asia-northeast1 \
  --allow-unauthenticated
```

## 🛠️ 開発環境のセットアップ

### 前提条件

- Node.js 18+
- Python 3.11+
- Docker
- Google Cloud CLI

### インストール

```bash
# リポジトリのクローン
git clone https://github.com/PheasantDevil/priceComparisonAppForIphone.git
cd priceComparisonAppForIphone

# フロントエンド依存関係のインストール
cd frontend
npm install

# バックエンド依存関係のインストール
cd ../backend
pip install -r requirements.txt

# 開発サーバーの起動
cd ../frontend
npm run dev          # フロントエンド (http://localhost:3000)

cd ../backend
python app.py        # バックエンド (http://localhost:5000)
```

## 📁 プロジェクト構造

```
priceComparisonAppForIphone/
├── frontend/                 # Next.js フロントエンド
│   ├── src/
│   │   ├── app/             # App Router
│   │   ├── components/      # React コンポーネント
│   │   └── lib/            # ユーティリティ
│   ├── package.json
│   ├── next.config.ts
│   └── vercel.json
├── backend/                  # Flask バックエンド
│   ├── app.py
│   └── requirements.txt
├── scripts/                  # データ管理スクリプト
├── .github/workflows/        # CI/CD 設定
├── vercel.json              # Vercel 設定
├── Dockerfile.cloudrun      # Cloud Run 用 Dockerfile
└── README.md
```

## 🔧 設定

### 環境変数

#### フロントエンド (Vercel)

```env
BACKEND_URL=https://price-comparison-app-asia-northeast1.run.app
```

#### バックエンド (Cloud Run)

```env
APP_ENV=production
USE_GOOGLE_CLOUD_STORAGE=true
BUCKET_NAME=price-comparison-app-data
GOOGLE_APPLICATION_CREDENTIALS_JSON=your-service-account-key
```

### GitHub Secrets

以下のシークレットを GitHub リポジトリに設定してください：

- `GCP_SA_KEY`: Google Cloud Service Account Key
- `GOOGLE_APPLICATION_CREDENTIALS_JSON`: Google Cloud 認証情報
- `VERCEL_TOKEN`: Vercel API Token
- `VERCEL_ORG_ID`: Vercel Organization ID
- `VERCEL_PROJECT_ID`: Vercel Project ID

## 🧪 テスト

```bash
# フロントエンドテスト
cd frontend
npm run test

# バックエンドテスト
cd backend
python -m pytest
```

## 📊 パフォーマンス

### フロントエンド (Vercel)

- **無料枠**: 月 100GB 帯域幅まで無料
- **パフォーマンス**: 高速 CDN 配信
- **自動デプロイ**: プッシュ時に自動更新
- **静的エクスポート**: 最適化された静的サイト

### バックエンド (Cloud Run)

- **無料枠**: 月 200 万リクエストまで無料
- **スケーリング**: 0〜10 インスタンスの自動スケーリング
- **可用性**: 99.9%の可用性保証

## 🔍 API エンドポイント

### ヘルスチェック

- `GET /health` - アプリケーションの健全性確認

### API ステータス

- `GET /api/status` - API サービスの状態確認

### 価格データ

- `GET /api/prices` - 価格データの取得
- `GET /get_prices` - レガシー価格データエンドポイント

## 🚀 デプロイメントフロー

1. **コードプッシュ** → GitHub Actions が自動実行
2. **テスト実行** → フロントエンド・バックエンドのテスト
3. **Cloud Run デプロイ** → バックエンドのデプロイ
4. **Vercel デプロイ** → フロントエンドのデプロイ
5. **ヘルスチェック** → デプロイメントの検証

## 📈 監視とログ

### Cloud Run ログ

```bash
gcloud logging read "resource.type=cloud_run_revision" --limit=50
```

### Vercel ログ

Vercel ダッシュボードでリアルタイムログを確認できます。

## 🔧 トラブルシューティング

### よくある問題

1. **フロントエンドビルドエラー**

   ```bash
   cd frontend
   npm run build
   ```

2. **バックエンド起動エラー**

   ```bash
   cd backend
   python app.py
   ```

3. **Cloud Run デプロイエラー**
   ```bash
   gcloud run services describe price-comparison-app --region=asia-northeast1
   ```

## 📝 ライセンス

MIT License

## 🤝 コントリビューション

1. フォークを作成
2. フィーチャーブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## 📞 サポート

問題が発生した場合は、GitHub Issues で報告してください。
