#!/bin/bash

echo "🚀 Building Next.js frontend..."

# スクリプトがbackendディレクトリから実行されることを前提とする
# プロジェクトルートに移動
cd "$(dirname "$0")/.."

# frontendディレクトリに移動
cd frontend

# 依存関係をインストール
npm install

# Next.jsをビルド
npm run build

echo "📁 Copying static files to templates directory..."

# プロジェクトルートに戻る
cd ..

# templatesディレクトリをクリア
rm -rf templates/*
mkdir -p templates

# Next.js 15の出力構造を確認
echo "🔍 Checking Next.js build output structure..."
if [ -d "frontend/.next" ]; then
  echo "📂 .next directory found"
  find frontend/.next -type d -maxdepth 3 | head -20
else
  echo "❌ .next directory not found"
  exit 1
fi

# Next.js 15では、静的ファイルは以下の場所に出力される可能性がある
# - HTMLファイル: frontend/out/ (static export)
# - 静的アセット: frontend/.next/static/

# まず、static exportのoutディレクトリを確認
if [ -d "frontend/out" ]; then
  echo "📋 Copying static files from frontend/out/ to templates/"
  cp -r frontend/out/* templates/
  echo "✅ Static files copied successfully from out/"
else
  echo "⚠️ frontend/out directory not found, trying .next/server/app"
  
  # 従来の方法を試す
  if [ -d "frontend/.next/server/app" ]; then
    echo "📋 Copying HTML files from frontend/.next/server/app/ to templates/"
    cp -r frontend/.next/server/app/* templates/
    echo "✅ HTML files copied successfully"
  else
    echo "❌ frontend/.next/server/app directory not found"
    echo "🔍 Available directories in .next:"
    find frontend/.next -type d -maxdepth 2
    exit 1
  fi
fi

# 静的アセットをコピー
if [ -d "frontend/.next/static" ]; then
  echo "📋 Copying static assets from frontend/.next/static/ to templates/_next/static/"
  mkdir -p templates/_next/static
  cp -r frontend/.next/static/* templates/_next/static/
  echo "✅ Static assets copied successfully"
else
  echo "⚠️ frontend/.next/static directory not found"
fi

echo "✅ Build and copy completed!"
echo "📊 Templates directory contents:"
ls -la templates/ 