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

# Next.js 15では、静的ファイルは以下の場所に出力される
# - HTMLファイル: frontend/.next/server/app/
# - 静的アセット: frontend/.next/static/

# HTMLファイルをコピー
if [ -d "frontend/.next/server/app" ]; then
  echo "📋 Copying HTML files from frontend/.next/server/app/ to templates/"
  cp -r frontend/.next/server/app/* templates/
  echo "✅ HTML files copied successfully"
else
  echo "❌ frontend/.next/server/app directory not found"
  exit 1
fi

# 静的アセットをコピー
if [ -d "frontend/.next/static" ]; then
  echo "📋 Copying static assets from frontend/.next/static/ to templates/_next/static/"
  mkdir -p templates/_next/static
  cp -r frontend/.next/static/* templates/_next/static/
  echo "✅ Static assets copied successfully"
else
  echo "❌ frontend/.next/static directory not found"
  exit 1
fi

echo "✅ Build and copy completed!"
echo "📊 Templates directory contents:"
ls -la templates/ 