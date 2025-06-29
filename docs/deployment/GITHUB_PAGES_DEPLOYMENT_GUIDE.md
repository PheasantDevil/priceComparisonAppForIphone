# GitHub Pages デプロイガイド

## 概要

Railway でのデプロイに問題があるため、GitHub Pages を代替プラットフォームとして設定しました。

## 利点

- ✅ **完全無料**: 月額料金なし
- ✅ **高安定性**: 静的サイトホスティング
- ✅ **自動デプロイ**: GitHub Actions で自動化
- ✅ **高速**: CDN 配信で高速アクセス

## 設定手順

### 1. GitHub Pages の有効化

1. GitHub リポジトリの "Settings" タブに移動
2. 左サイドバーの "Pages" をクリック
3. "Source" で "GitHub Actions" を選択
4. "Save" をクリック

### 2. 環境変数の設定

1. GitHub リポジトリの "Settings" → "Secrets and variables" → "Actions"
2. "New repository secret" をクリック
3. 以下のシークレットを追加：
   ```
   Name: NEXT_PUBLIC_API_URL
   Value: https://your-api-endpoint.com
   ```

### 3. デプロイの実行

1. `main` ブランチにプッシュ
2. GitHub Actions が自動的に実行される
3. デプロイ完了後、以下の URL でアクセス可能：
   ```
   https://pheasantdevil.github.io/priceComparisonAppForIphone/
   ```

## 技術的な変更点

### Next.js 設定

- `output: 'export'` - 静的ファイル生成
- `basePath` - GitHub Pages 用のベースパス設定
- `trailingSlash: true` - 末尾スラッシュ対応

### ワークフロー

- 静的サイトビルド
- GitHub Pages 用のアーティファクトアップロード
- 自動デプロイ

### 404 対応

- SPA 用の 404 ページ
- クライアントサイドルーティング対応

## トラブルシューティング

### ビルドエラー

```bash
# ローカルでビルドテスト
cd frontend
npm run build
```

### パスエラー

- `basePath` 設定を確認
- 相対パスを絶対パスに変更

### API 接続エラー

- `NEXT_PUBLIC_API_URL` 環境変数を確認
- CORS 設定を確認

## 期待される結果

- 高速な静的サイト
- 安定したデプロイ
- ローカルと同じ機能
- 無料での運用
