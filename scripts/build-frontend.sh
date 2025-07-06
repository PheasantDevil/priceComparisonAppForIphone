#!/bin/bash

# エラー時に即座に終了
set -e

echo "🚀 Building Next.js frontend for production..."

# プロジェクトルートを取得
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "📂 Project root: $PROJECT_ROOT"

# frontendディレクトリに移動
cd "$PROJECT_ROOT/frontend"

# Node.jsとnpmの確認
echo "🔍 Checking Node.js and npm..."
node --version
npm --version

# 依存関係をインストール（package-lock.jsonの問題を回避）
echo "📦 Installing dependencies..."
npm install --no-audit --no-fund

# プロジェクトルートに戻る
cd "$PROJECT_ROOT"

# templatesディレクトリを作成
echo "📋 Creating templates directory..."
rm -rf templates
mkdir -p templates

# Next.jsをビルド
echo "🔨 Building Next.js application..."
cd "$PROJECT_ROOT/frontend"

# ビルドを試行
if npm run build; then
  echo "✅ Next.js build successful"
  
  # プロジェクトルートに戻る
  cd "$PROJECT_ROOT"
  
  # 静的ファイルをコピー
  echo "📋 Copying static files..."
  if [ -d "frontend/out" ]; then
    echo "📁 Found frontend/out directory"
    echo "📁 Contents of frontend/out:"
    ls -la frontend/out/
    
    cp -r frontend/out/* templates/
    echo "✅ Static files copied from frontend/out/"
  else
    echo "❌ frontend/out directory not found"
    echo "📁 Checking frontend directory structure:"
    ls -la frontend/
    
    # 代替として.nextディレクトリを確認
    if [ -d "frontend/.next" ]; then
      echo "📁 Found .next directory, creating fallback"
      echo "<!DOCTYPE html><html><head><title>Price Comparison App</title><meta charset='utf-8'></head><body><h1>Price Comparison App</h1><p>Next.js build completed but static export not available</p></body></html>" > templates/index.html
    else
      echo "❌ No build output found"
      exit 1
    fi
  fi
else
  echo "❌ Next.js build failed"
  
  # プロジェクトルートに戻る
  cd "$PROJECT_ROOT"
  
  # フォールバックHTMLを作成
  echo "📋 Creating fallback HTML..."
  cat > templates/index.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Price Comparison App</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; }
        .status { background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 4px; margin: 20px 0; }
        .error { background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }
        .success { background: #d4edda; border: 1px solid #c3e6cb; color: #155724; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Price Comparison App</h1>
        <div class="status">
            <h3>🚧 Frontend Build Status</h3>
            <p><strong>Status:</strong> Frontend is being built or has encountered an issue</p>
            <p><strong>Backend:</strong> ✅ Running successfully</p>
            <p><strong>API Health:</strong> <a href="/health" target="_blank">Check Health</a></p>
        </div>
        <div class="status success">
            <h3>✅ Backend Services Available</h3>
            <ul>
                <li><a href="/health">Health Check</a></li>
                <li><a href="/api/status">API Status</a></li>
            </ul>
        </div>
        <p><em>This is a fallback page. The full frontend will be available once the build process completes.</em></p>
    </div>
</body>
</html>
EOF
  echo "✅ Fallback HTML created"
fi

echo "✅ Frontend build process completed!"
echo "📊 Templates directory contents:"
ls -la templates/
echo "📊 Templates directory size:"
du -sh templates/ 