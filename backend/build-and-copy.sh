#!/bin/bash

echo "🚀 Building Next.js frontend..."
cd frontend

# 依存関係をインストール
npm install

# Next.jsをビルド
npm run build

# 静的ファイルをエクスポート（Next.js 13以降は不要、buildで自動生成）
# npm run export

echo "📁 Copying static files to templates directory..."
cd ..

# templatesディレクトリをクリア
rm -rf templates/*
mkdir -p templates

# 静的ファイルをコピー
cp -r frontend/out/* templates/ 2>/dev/null || cp -r frontend/.next/static/* templates/ 2>/dev/null || echo "Static files not found in expected location"

echo "✅ Build and copy completed!"
echo "📊 Templates directory contents:"
ls -la templates/ 