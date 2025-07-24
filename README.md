# Price Comparison App for iPhone

価格比較アプリケーション - iPhone 製品の価格を比較・追跡するための Web アプリケーション

## 🏗️ アーキテクチャ

このアプリケーションは **Vercel + GCP（Cloud Functions）** のサーバーレスアーキテクチャを採用しています：

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
# 例: get_prices 関数のデプロイ
cd functions/get_prices
gcloud functions deploy get_prices \
  --runtime python311 \
  --trigger-http \
  --allow-unauthenticated \
  --entry-point get_prices \
  --region asia-northeast1

# 他の関数も同様にデプロイ
cd ../get_price_history
gcloud functions deploy get_price_history \
  --runtime python311 \
  --trigger-http \
  --allow-unauthenticated \
  --entry-point get_price_history \
  --region asia-northeast1

cd ../api_prices
gcloud functions deploy api_prices \
  --runtime python311 \
  --trigger-http \
  --allow-unauthenticated \
  --entry-point api_prices \
  --region asia-northeast1

cd ../api_status
gcloud functions deploy api_status \
  --runtime python311 \
  --trigger-http \
  --allow-unauthenticated \
  --entry-point api_status \
  --region asia-northeast1

cd ../health
gcloud functions deploy health \
  --runtime python311 \
  --trigger-http \
  --allow-unauthenticated \
  --entry-point health \
  --region asia-northeast1

cd ../scrape_prices
gcloud functions deploy scrape_prices \
  --runtime python311 \
  --trigger-http \
  --allow-unauthenticated \
  --entry-point scrape_prices \
  --region asia-northeast1

cd ../set_alert
gcloud functions deploy set_alert \
  --runtime python311 \
  --trigger-http \
  --allow-unauthenticated \
  --entry-point set_alert \
  --region asia-northeast1

cd ../check_prices
gcloud functions deploy check_prices \
  --runtime python311 \
  --trigger-http \
  --allow-unauthenticated \
  --entry-point check_prices \
  --region asia-northeast1
```

#### ローカルテスト

```bash
# Cloud Functions Frameworkのインストール
pip install functions-framework

# ローカル起動（例: get_prices）
cd functions/get_prices
export PORT=8080
functions-framework --target=get_prices

# 動作確認
curl "http://localhost:8080?series=iPhone15"
```

---

## 🛠️ 開発環境のセットアップ

### 前提条件

- Node.js 18+
- Python 3.11+
- Google Cloud CLI
- Google Cloud SDK

### インストール

```bash
# リポジトリのクローン
git clone https://github.com/PheasantDevil/priceComparisonAppForIphone.git
cd priceComparisonAppForIphone

# フロントエンド依存関係のインストール
cd frontend
npm install

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
│   │   └── lib/            # ユーティリティ・API
│   ├── package.json
│   ├── next.config.ts
│   └── vercel.json
├── functions/                # Cloud Functions用API
│   ├── get_prices/          # 価格データ取得
│   ├── get_price_history/   # 価格履歴取得
│   ├── api_prices/          # 公式価格取得
│   ├── api_status/          # APIステータス
│   ├── health/              # ヘルスチェック
│   ├── scrape_prices/       # 価格スクレイピング
│   ├── set_alert/           # アラート設定
│   └── check_prices/        # 価格チェック
├── scripts/                  # データ管理スクリプト
├── backend/                  # 旧Flaskバックエンド（参考用）
├── .github/workflows/        # CI/CD 設定
├── vercel.json              # Vercel 設定
└── README.md
```

---

## 🔧 設定

### 環境変数

#### フロントエンド (Vercel)

```env
# Cloud FunctionsのベースURL
BACKEND_URL=https://asia-northeast1-price-comparison-app.cloudfunctions.net
NEXT_PUBLIC_API_BASE_URL=https://asia-northeast1-price-comparison-app.cloudfunctions.net
```

#### Cloud Functions

```env
GOOGLE_APPLICATION_CREDENTIALS_JSON=your-service-account-key
BUCKET_NAME=price-comparison-app-data
```

---

## 🔍 API エンドポイント

### Cloud Functions

- `GET /get_prices` - 価格データの取得
- `GET /get_price_history` - 価格推移データの取得
- `GET /api_prices` - 公式価格データの取得
- `GET /api_status` - API ステータスの確認
- `GET /health` - ヘルスチェック
- `POST /scrape_prices` - 価格スクレイピングの実行
- `POST /set_alert` - 価格アラートの設定
- `GET /check_prices` - 価格チェックの実行

### Vercel プロキシ設定

Vercel の`vercel.json`で Cloud Functions へのプロキシ設定を行っています：

```json
{
  "routes": [
    {
      "src": "/get_prices",
      "dest": "https://asia-northeast1-price-comparison-app.cloudfunctions.net/get_prices"
    }
    // ... 他のエンドポイント
  ]
}
```

---

## 📈 監視とログ

### Cloud Functions ログ

```bash
# 特定の関数のログを確認
gcloud functions logs read get_prices --region=asia-northeast1 --limit=50

# 全関数のログを確認
gcloud functions logs read --region=asia-northeast1 --limit=50
```

### Vercel ログ

Vercel ダッシュボードでリアルタイムログを確認できます。

---

## 🔧 トラブルシューティング

### よくある問題

1. **フロントエンドビルドエラー**

   ```bash
   cd frontend
   npm run build
   ```

2. **Cloud Functions デプロイエラー**

   ```bash
   # 関数の状態確認
   gcloud functions describe get_prices --region=asia-northeast1

   # ログ確認
   gcloud functions logs read get_prices --region=asia-northeast1
   ```

3. **API 接続エラー**

   ```bash
   # Cloud Functionsの直接テスト
   curl "https://asia-northeast1-price-comparison-app.cloudfunctions.net/get_prices?series=iPhone15"
   ```

---

## 🚀 移行完了

- ✅ Cloud Run/Flask から Cloud Functions への完全移行完了
- ✅ 全 API エンドポイントが Cloud Functions で提供
- ✅ フロントエンドの API 呼び出し先を Cloud Functions に統一
- ✅ Vercel プロキシ設定でシームレスな統合

---

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
