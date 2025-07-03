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

# 依存関係をインストール
echo "📦 Installing dependencies..."
npm ci --include=dev --no-audit --no-fund

# Next.jsをビルド
echo "🔨 Building Next.js application..."
npm run build

# プロジェクトルートに戻る
cd "$PROJECT_ROOT"

# templatesディレクトリを作成
echo "📋 Creating templates directory..."
rm -rf templates
mkdir -p templates

# 静的ファイルをコピー
echo "📋 Copying static files..."
if [ -d "frontend/out" ]; then
  cp -r frontend/out/* templates/
  echo "✅ Static files copied from frontend/out/"
else
  echo "❌ frontend/out directory not found"
  exit 1
fi

echo "✅ Frontend build completed!"
echo "📊 Templates directory contents:"
ls -la templates/ 