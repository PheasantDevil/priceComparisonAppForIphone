#!/bin/bash

echo "🚀 Building Next.js frontend..."

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

echo "📂 Project root: $PROJECT_ROOT"

# プロジェクトルートの内容を確認
echo "📂 Project root contents:"
ls -la "$PROJECT_ROOT"

# frontendディレクトリの存在確認
if [ ! -d "$PROJECT_ROOT/frontend" ]; then
  echo "❌ frontend directory not found in project root"
  echo "🔍 Available directories:"
  ls -la "$PROJECT_ROOT"
  exit 1
fi

echo "✅ frontend directory found"

# frontendディレクトリに移動
cd "$PROJECT_ROOT/frontend"

# 依存関係をインストール
npm install

# Next.jsをビルド
npm run build

echo "📁 Copying static files to templates directory..."

# 現在のディレクトリを確認（ビルド後）
echo "📂 Current directory after build: $(pwd)"
echo "📂 Current directory contents after build:"
ls -la

# プロジェクトルートに戻る
cd "$PROJECT_ROOT"

# ビルド後のディレクトリ状態を確認
echo "📂 Post-build project root contents:"
ls -la

# templatesディレクトリをクリア
rm -rf templates/*
mkdir -p templates

# Next.js 15の静的エクスポート出力を確認
echo "🔍 Checking Next.js build output structure..."

# frontendディレクトリの内容を確認
echo "📂 frontend directory contents:"
ls -la frontend/

# まず、static exportのoutディレクトリを確認（Next.js 15のoutput: 'export'）
if [ -d "frontend/out" ]; then
  echo "📋 Copying static files from frontend/out/ to templates/"
  cp -r frontend/out/* templates/
  echo "✅ Static files copied successfully from out/"
else
  echo "⚠️ frontend/out directory not found, checking .next directory"
  
  # .nextディレクトリの確認
  if [ -d "frontend/.next" ]; then
    echo "📂 .next directory found"
    find frontend/.next -type d -maxdepth 3 | head -20
    
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
    
    # 静的アセットをコピー
    if [ -d "frontend/.next/static" ]; then
      echo "📋 Copying static assets from frontend/.next/static/ to templates/_next/static/"
      mkdir -p templates/_next/static
      cp -r frontend/.next/static/* templates/_next/static/
      echo "✅ Static assets copied successfully"
    else
      echo "⚠️ frontend/.next/static directory not found"
    fi
  else
    echo "❌ Neither frontend/out nor frontend/.next directory found"
    echo "🔍 Available directories in frontend:"
    ls -la frontend/
    exit 1
  fi
fi

echo "✅ Build and copy completed!"
echo "📊 Templates directory contents:"
ls -la templates/ 