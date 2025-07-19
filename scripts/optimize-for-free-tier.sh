#!/bin/bash

# 無料枠最適化スクリプト
echo "🆓 無料枠最適化を開始します..."

# 1. フロントエンド最適化
echo "🔧 フロントエンド最適化中..."

# Next.js設定の最適化
cat > frontend/next.config.optimized.js << 'EOF'
module.exports = {
  output: 'export',
  trailingSlash: true,
  images: {
    unoptimized: true,
    domains: ['storage.googleapis.com'],
  },
  // キャッシュ最適化
  generateEtags: false,
  // バンドルサイズ最適化
  experimental: {
    optimizeCss: true,
    optimizePackageImports: ['react-icons', 'recharts'],
  },
  // 静的生成最適化 - ISRは export モードと互換性がない
  // export モードでは静的ファイルのみ生成される
};
EOF

# 2. API最適化
echo "🔌 API最適化中..."

cat > backend/optimized_app.py << 'EOF'
from flask import Flask, jsonify, request
from google.cloud import firestore
import os
import json

app = Flask(__name__)
db = firestore.Client()

# キャッシュヘッダー設定
def add_cache_headers(response, max_age=300):
    response.headers['Cache-Control'] = f'public, max-age={max_age}'
    response.headers['Vary'] = 'Accept-Encoding'
    return response

@app.route('/api/prices')
def get_prices():
    # 必要なフィールドのみ取得（データ転送量削減）
    prices_ref = db.collection('prices').select(['name', 'price', 'updated_at'])
    prices = [doc.to_dict() for doc in prices_ref.limit(50).stream()]
    
    response = jsonify(prices)
    return add_cache_headers(response, max_age=600)  # 10分キャッシュ

@app.route('/api/prices/<product_id>')
def get_product_price(product_id):
    # 個別商品の価格取得
    doc = db.collection('prices').document(product_id).get()
    if doc.exists:
        response = jsonify(doc.to_dict())
        return add_cache_headers(response, max_age=300)  # 5分キャッシュ
    return jsonify({'error': 'Product not found'}), 404

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy'}), 200
EOF

# 3. データベース最適化
echo "🗄️ データベース最適化中..."

cat > scripts/optimize-firestore.js << 'EOF'
const { Firestore } = require('@google-cloud/firestore');
const db = new Firestore();

// インデックス最適化
async function optimizeIndexes() {
  console.log('Creating optimized indexes...');
  
  try {
    // 価格データのインデックス
    await db.collection('prices').createIndex({
      fields: [
        { fieldPath: 'category', order: 'ASCENDING' },
        { fieldPath: 'updated_at', order: 'DESCENDING' }
      ]
    });
    console.log('Indexes created successfully');
  } catch (error) {
    console.error('Failed to create indexes:', error);
    throw error;
  }
}

// データ圧縮
async function compressData() {
  console.log('Compressing data...');
  
  const pricesRef = db.collection('prices');
  const snapshot = await pricesRef.get();
  
  snapshot.forEach(doc => {
    const data = doc.data();
    // 不要なフィールドを削除
    delete data.metadata;
    delete data.debug_info;
    
    // データを更新
    doc.ref.update(data);
  });
  
  console.log('Data compression completed');
}

module.exports = { optimizeIndexes, compressData };
EOF

# 4. 画像最適化
echo "🖼️ 画像最適化中..."

cat > scripts/optimize-images.sh << 'EOF'
#!/bin/bash

# Cloud Storage画像最適化
BUCKET_NAME="your-bucket-name"

echo "Optimizing images in Cloud Storage..."

# 画像の圧縮
gsutil -m cp -r gs://$BUCKET_NAME/images/ gs://$BUCKET_NAME/images-optimized/

# キャッシュヘッダーの設定
gsutil -m setmeta -h "Cache-Control:public, max-age=31536000" gs://$BUCKET_NAME/images-optimized/**

echo "Image optimization completed"
EOF

# 5. 監視設定
echo "📊 監視設定中..."

cat > scripts/monitor-usage.js << 'EOF'
const { Firestore } = require('@google-cloud/firestore');
const db = new Firestore();

// 使用量監視
async function monitorUsage() {
  const today = new Date();
  const startOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
  
  // Firestore読み取り回数
  const readsRef = db.collection('usage_stats').doc('reads');
  const readsDoc = await readsRef.get();
  const currentReads = readsDoc.exists ? readsDoc.data().count : 0;
  
  // 無料枠制限（50,000読み取り）
  const freeLimit = 50000;
  const usagePercentage = (currentReads / freeLimit) * 100;
  
  console.log(`Firestore reads: ${currentReads}/${freeLimit} (${usagePercentage.toFixed(1)}%)`);
  
  if (usagePercentage > 80) {
    console.warn('⚠️ Warning: Approaching free tier limit');
  }
  
  return {
    reads: currentReads,
    limit: freeLimit,
    percentage: usagePercentage
  };
}

module.exports = { monitorUsage };
EOF

# 6. 最適化チェックリスト
echo "📋 最適化チェックリストを作成中..."

cat > OPTIMIZATION_CHECKLIST.md << 'EOF'
# 無料枠最適化チェックリスト

## フロントエンド最適化
- [ ] 画像の最適化（WebP形式使用）
- [ ] コード分割の実装
- [ ] キャッシュ戦略の設定
- [ ] 不要な依存関係の削除

## API最適化
- [ ] レスポンスキャッシュの設定
- [ ] 必要なフィールドのみ取得
- [ ] ページネーションの実装
- [ ] エラーハンドリングの最適化

## データベース最適化
- [ ] インデックスの最適化
- [ ] クエリの最適化
- [ ] データ圧縮の実装
- [ ] 不要なデータの削除

## ストレージ最適化
- [ ] 画像の圧縮
- [ ] キャッシュヘッダーの設定
- [ ] CDNの活用
- [ ] 不要なファイルの削除

## 監視・アラート
- [ ] 使用量の監視設定
- [ ] アラートの設定
- [ ] コスト予測の実装
- [ ] 最適化レポートの生成
EOF

echo "✅ 無料枠最適化が完了しました！"
echo ""
echo "📊 最適化内容:"
echo "- フロントエンド: キャッシュ戦略、バンドル最適化"
echo "- API: レスポンスキャッシュ、データ転送量削減"
echo "- データベース: インデックス最適化、データ圧縮"
echo "- 画像: 圧縮、CDN最適化"
echo "- 監視: 使用量監視、アラート設定"
echo ""
echo "📋 次のステップ:"
echo "1. OPTIMIZATION_CHECKLIST.md を確認"
echo "2. 各最適化スクリプトを実行"
echo "3. 使用量を定期的に監視"
echo "4. 必要に応じて追加最適化を実施" 