# Price Comparison App for iPhone

価格比較アプリケーション - iPhone 製品の価格を比較・追跡するための Web アプリケーション

## 🏗️ アーキテクチャ

このアプリケーションは **Vercel + GCP（Cloud Functions）** のハイブリッドアーキテクチャを採用しています：

- **フロントエンド**: Vercel (Next.js 15.3.3)
- **バックエンド**: Google Cloud Functions (Python)
- **データベース**: Firestore
- **ストレージ**: Cloud Storage
- **CI/CD**: GitHub Actions

---

## 🚀 デプロイメント

### フロントエンド (Vercel)

フロントエンドは Vercel に自動デプロイされます：

```bash
# 手動デプロイ（必要な場合）
cd frontend
vercel --prod
```

### バックエンド (Cloud Functions)

#### Cloud Functions へのデプロイ

```bash
# 例: /functions/get_prices デプロイ
cd functions/get_prices
# GCPプロジェクト・認証設定済み前提
# main.py の get_prices 関数をエントリポイントとしてデプロイ

gcloud functions deploy get_prices \
  --runtime python311 \
  --trigger-http \
  --allow-unauthenticated \
  --entry-point get_prices
```

#### ローカルテスト

```bash
# Cloud Functions Frameworkのインストール
pip install functions-framework

# ローカル起動
export PORT=8080
functions-framework --target=get_prices

# 動作確認
curl "http://localhost:8080"
```

---

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

# Cloud Functions依存関係のインストール（例: get_prices）
cd ../functions/get_prices
pip install -r requirements.txt

# 開発サーバーの起動
cd ../frontend
npm run dev          # フロントエンド (http://localhost:3000)

# Cloud Functionsローカル起動例
cd ../functions/get_prices
functions-framework --target=get_prices
```

---

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
├── backend/                  # Flask バックエンド（Cloud Runから移行中）
│   ├── app.py
│   └── requirements.txt
├── functions/                # Cloud Functions用API
│   └── get_prices/
│       └── main.py
├── scripts/                  # データ管理スクリプト
├── .github/workflows/        # CI/CD 設定
├── vercel.json              # Vercel 設定
├── Dockerfile.cloudrun      # Cloud Run 用 Dockerfile（旧）
└── README.md
```

---

## 🔧 設定

### 環境変数

#### フロントエンド (Vercel)

```env
# Cloud Functionsのエンドポイントを直接指定
BACKEND_URL=https://REGION-PROJECT_ID.cloudfunctions.net/get_prices
```

#### Cloud Functions

```env
GOOGLE_APPLICATION_CREDENTIALS_JSON=your-service-account-key
BUCKET_NAME=price-comparison-app-data
```

---

## 🔍 API エンドポイント

### Cloud Functions

- `GET /get_prices` - 価格データの取得（Cloud Functions で提供）
- `GET /get_price_history` - 価格推移データの取得（Cloud Functions で提供）

---

## 🚀 移行メモ

- Cloud Run/Flask から Cloud Functions への API 移行を順次進行中
- `/get_prices`エンドポイントは Cloud Functions で提供されるようになりました
- フロントエンドの API 呼び出し先も Cloud Functions エンドポイントに統一予定

---

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
