#!/bin/bash

# エラー時に即座に終了
set -e

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
echo "📂 Moved to frontend directory: $(pwd)"

# Node.jsとnpmの確認
echo "🔍 Checking Node.js and npm..."
node --version || echo "❌ Node.js not found"
npm --version || echo "❌ npm not found"

# package.jsonの確認
if [ ! -f "package.json" ]; then
  echo "❌ package.json not found in frontend directory"
  ls -la
  exit 1
fi

echo "✅ package.json found"

# 依存関係をインストール
echo "📦 Installing dependencies..."
npm install || {
  echo "❌ npm install failed"
  exit 1
}

echo "✅ Dependencies installed successfully"

# Next.jsをビルド
echo "🔨 Building Next.js application..."
npm run build || {
  echo "❌ npm run build failed"
  exit 1
}

echo "✅ Next.js build completed successfully"

echo "📁 Copying static files to templates directory..."

# 現在のディレクトリを確認（ビルド後）
echo "📂 Current directory after build: $(pwd)"
echo "📂 Current directory contents after build:"
ls -la

# プロジェクトルートに戻る（絶対パスを使用）
echo "📂 Returning to project root..."
cd "$PROJECT_ROOT"
echo "📂 Current directory after return: $(pwd)"

# プロジェクトルートにいることを確認
if [ "$(pwd)" != "$PROJECT_ROOT" ]; then
  echo "❌ Failed to return to project root"
  echo "Current: $(pwd), Expected: $PROJECT_ROOT"
  exit 1
fi

echo "✅ Successfully returned to project root"

# ビルド後のディレクトリ状態を確認
echo "📂 Post-build project root contents:"
ls -la

# templatesディレクトリをクリア
echo "🧹 Clearing templates directory..."
rm -rf templates/*
mkdir -p templates
echo "✅ Templates directory cleared and created"

# Next.js 15の静的エクスポート出力を確認
echo "🔍 Checking Next.js build output structure..."

# 現在のディレクトリを確認
CURRENT_DIR=$(pwd)
echo "📂 Current working directory: $CURRENT_DIR"

# プロジェクトルートにいることを確認
if [ "$CURRENT_DIR" = "$PROJECT_ROOT" ]; then
  echo "📂 Currently in project root, checking frontend/out and frontend/.next"
  
  # frontendディレクトリの内容を確認
  echo "📂 frontend directory contents:"
  ls -la frontend/

  # まず、static exportのoutディレクトリを確認（Next.js 15のoutput: 'export'）
  if [ -d "frontend/out" ]; then
    echo "📋 Copying static files from frontend/out/ to templates/"
    cp -r frontend/out/* templates/ || {
      echo "❌ Failed to copy files from frontend/out/"
      exit 1
    }
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
        cp -r frontend/.next/server/app/* templates/ || {
          echo "❌ Failed to copy files from frontend/.next/server/app/"
          exit 1
        }
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
        cp -r frontend/.next/static/* templates/_next/static/ || {
          echo "❌ Failed to copy static assets"
          exit 1
        }
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
else
  echo "❌ Not in project root. Current: $CURRENT_DIR, Expected: $PROJECT_ROOT"
  exit 1
fi

echo "✅ Build and copy completed!"
echo "📊 Templates directory contents:"
ls -la templates/
echo "🎉 All operations completed successfully!" 