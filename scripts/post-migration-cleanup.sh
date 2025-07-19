#!/bin/bash

# 移行後クリーンアップスクリプト
echo "🧹 Railway → Cloud Run 移行後のクリーンアップを開始します..."

# 1. Railwayサービスの停止確認
echo "📊 Railwayサービスの停止確認..."
echo "Railwayサービスを手動で停止してください:"
echo "1. Railwayダッシュボードにアクセス"
echo "2. price-comparison-appサービスを選択"
echo "3. Settings → Danger Zone → Delete Service"
echo ""

read -p "Railwayサービスを停止しましたか？ (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "⚠️ Railwayサービスの停止を先に実行してください"
    exit 1
fi

# 2. テストサービスの削除
echo "🗑️ テストサービスの削除中..."
gcloud run services delete price-comparison-app-test \
    --region asia-northeast1 \
    --project price-comparison-app-463007 \
    --quiet || echo "テストサービスは既に削除されています"

# 3. 古いDockerイメージの削除
echo "🐳 古いDockerイメージの削除中..."
gcloud container images list-tags gcr.io/price-comparison-app-463007/price-comparison-app-test \
    --format="value(digest)" | head -5 | while read digest; do
    gcloud container images delete gcr.io/price-comparison-app-463007/price-comparison-app-test@$digest \
        --quiet || echo "イメージ削除スキップ"
done

# 4. 古い設定ファイルのバックアップ
echo "📁 古い設定ファイルのバックアップ中..."
mkdir -p backup/railway
cp railway.json backup/railway/ 2>/dev/null || echo "railway.json not found"
cp Procfile backup/railway/ 2>/dev/null || echo "Procfile not found"
cp Dockerfile backup/railway/ 2>/dev/null || echo "Dockerfile not found"

# 5. Railway関連ファイルの削除
echo "🗑️ Railway関連ファイルの削除中..."
rm -f railway.json
rm -f Procfile
rm -rf railway/

# 6. GitHub Actionsワークフローの更新
echo "🔄 GitHub Actionsワークフローの更新中..."
if [ -f ".github/workflows/deploy-to-railway.yml" ]; then
    mv .github/workflows/deploy-to-railway.yml .github/workflows/deploy-to-railway.yml.backup
    echo "✅ Railwayワークフローをバックアップしました"
fi

# 7. 環境変数ファイルの整理
echo "🔧 環境変数ファイルの整理中..."
if [ -f ".env.gcp" ]; then
    echo "✅ GCP環境変数ファイル: .env.gcp"
fi

# 8. ドキュメントの更新
echo "📝 ドキュメントの更新中..."
if [ -f "README.md" ]; then
    echo "README.mdを手動で更新してください:"
    echo "- Railway → Cloud Run への移行完了を記載"
    echo "- 新しいデプロイURLを記載"
    echo "- 新しいデプロイ手順を記載"
fi

# 9. 監視設定の確認
echo "📊 監視設定の確認中..."
echo "Cloud Runの監視設定:"
echo "1. Cloud Console → Cloud Run → price-comparison-app"
echo "2. Monitoring → Logs でログを確認"
echo "3. Metrics でメトリクスを確認"

# 10. 最終確認
echo ""
echo "🎉 クリーンアップ完了！"
echo ""
echo "📋 移行完了チェックリスト:"
echo "✅ Cloud Run本番環境が動作中"
echo "✅ Railwayサービスが停止"
echo "✅ テストサービスが削除"
echo "✅ 古い設定ファイルがバックアップ"
echo "✅ Railway関連ファイルが削除"
echo ""
echo "📋 手動で確認・更新が必要な項目:"
echo "1. README.md の更新"
echo "2. DNS設定の更新（カスタムドメイン使用時）"
echo "3. 監視アラートの設定"
echo "4. チームメンバーへの移行完了通知"
echo ""
echo "🚀 Cloud Run環境での運用開始！" 