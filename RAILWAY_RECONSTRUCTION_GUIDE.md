# Railway サービス再構築ガイド

## 現在の問題

- 複数のサービスが存在し、正しいサービス名が不明
- Next.js ビルドエラーが継続
- デプロイが失敗している

## 完全再構築の手順

### 1. Railway ダッシュボードで既存サービスを削除

1. https://railway.app/dashboard にアクセス
2. プロジェクト "price-comparison-app" を選択
3. 各サービスを選択して "Delete Service" を実行
4. すべてのサービスを削除

### 2. 新しいサービスを作成

1. "New Service" → "GitHub Repo" を選択
2. `PheasantDevil/priceComparisonAppForIphone` を選択
3. "Deploy Now" をクリック

### 3. 自動設定の確認

- Railway が自動的に Next.js プロジェクトを検出
- `frontend/` ディレクトリを自動認識
- 適切なビルド・デプロイ設定が適用される

### 4. 環境変数の設定

```
NODE_ENV=production
NEXT_PUBLIC_API_URL=https://your-api-url.com
```

### 5. デプロイの確認

- ビルドログで Next.js のビルドが成功することを確認
- アプリケーションが正常に起動することを確認

## 期待される結果

- シンプルな単一サービス構成
- Next.js アプリケーションの正常な動作
- ローカルと同じ内容の表示
