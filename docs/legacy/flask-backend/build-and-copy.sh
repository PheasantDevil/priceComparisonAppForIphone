#!/bin/bash

# エラー時に即座に終了
set -e

# タイムアウト設定（Railway環境での問題を防ぐ）
TIMEOUT=600  # 10分

echo "🚀 Building Next.js frontend..."
echo "⏰ Timeout set to ${TIMEOUT} seconds"

# 現在のディレクトリを確認
echo "📂 Current directory: $(pwd)"
echo "📂 Current directory contents:"
ls -la

# プロジェクトルートを確実に特定
if [ -f "backend/build-and-copy.sh" ]; then
  # backendディレクトリから実行された場合
  PROJECT_ROOT="$(dirname "$(dirname "$0")")"
  echo "📂 Detected: running from backend directory"
elif [ -f "build-and-copy.sh" ]; then
  # プロジェクトルートから実行された場合
  PROJECT_ROOT="$(pwd)"
  echo "📂 Detected: running from project root"
else
  echo "❌ build-and-copy.sh not found in expected locations"
  echo "🔍 Searching for build-and-copy.sh..."
  find . -name "build-and-copy.sh" 2>/dev/null || echo "No build-and-copy.sh found"
  exit 1
fi

# プロジェクトルートを絶対パスに変換
PROJECT_ROOT=$(realpath "$PROJECT_ROOT")
echo "📂 Project root (absolute): $PROJECT_ROOT"

# frontendディレクトリの存在確認
if [ ! -d "$PROJECT_ROOT/frontend" ]; then
  echo "❌ frontend directory not found in project root"
  exit 1
fi

echo "✅ frontend directory found"

# frontendディレクトリに移動
cd "$PROJECT_ROOT/frontend"
echo "📂 Moved to frontend directory: $(pwd)"

# Node.jsとnpmの確認
echo "🔍 Checking Node.js and npm..."
node --version || echo "❌ Node.js not found"
npm --version || echo "❌ npm not found"

# package.jsonの確認
if [ ! -f "package.json" ]; then
  echo "❌ package.json not found in frontend directory"
  exit 1
fi

echo "✅ package.json found"

# 依存関係をインストール（タイムアウト付き）
echo "📦 Installing dependencies..."
timeout $TIMEOUT npm ci --include=dev || {
  echo "❌ npm install failed or timed out"
  echo "🔍 Checking npm cache and retrying..."
  npm cache clean --force
  timeout $TIMEOUT npm ci --include=dev || {
    echo "❌ npm install failed after retry"
    exit 1
  }
}

echo "✅ Dependencies installed successfully"

# Next.jsをビルド（静的エクスポート）
echo "🔨 Building Next.js application..."
timeout $TIMEOUT npm run build || {
  echo "❌ npm run build failed or timed out"
  echo "🔍 Checking build configuration..."
  cat package.json | grep -A 10 -B 5 "scripts"
  exit 1
}

echo "✅ Next.js build completed successfully"

# プロジェクトルートに戻る
cd "$PROJECT_ROOT"
echo "📂 Returned to project root: $(pwd)"

# templatesディレクトリをクリアして作成
echo "🧹 Clearing templates directory..."
rm -rf templates
mkdir -p templates
echo "✅ Templates directory cleared and created"

# Next.js 15の静的エクスポート出力をコピー
echo "📋 Copying static files from frontend/out/ to templates/"
if [ -d "frontend/out" ]; then
  cp -r frontend/out/* templates/ || {
    echo "❌ Failed to copy files from frontend/out/"
    exit 1
  }
  echo "✅ Static files copied successfully from out/"
elif [ -d "frontend/dist" ]; then
  cp -r frontend/dist/* templates/ || {
    echo "❌ Failed to copy files from frontend/dist/"
    exit 1
  }
  echo "✅ Static files copied successfully from dist/"
else
  echo "❌ frontend/out or frontend/dist directory not found after build"
  echo "🔍 Available directories in frontend:"
  ls -la frontend/
  echo "🔍 Checking for other possible output directories:"
  find frontend/ -type d -name "out" -o -name "dist" -o -name "build" 2>/dev/null || echo "No output directories found"
  exit 1
fi

echo "✅ Build and copy completed!"
echo "📊 Templates directory contents:"
ls -la templates/
echo "🎉 All operations completed successfully!" 