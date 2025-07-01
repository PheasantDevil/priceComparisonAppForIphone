#!/bin/bash

# Railwayログ監視スクリプトの実行

set -e

# スクリプトのディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "Starting Railway Log Monitor..."
echo "Project root: $PROJECT_ROOT"

# 環境変数の確認
if [ -z "$SLACK_WEBHOOK_URL" ]; then
    echo "Error: SLACK_WEBHOOK_URL environment variable is required"
    exit 1
fi

if [ -z "$RAILWAY_PROJECT_ID" ]; then
    echo "Error: RAILWAY_PROJECT_ID environment variable is required"
    exit 1
fi

# Railway CLIがインストールされているか確認
if ! command -v railway &> /dev/null; then
    echo "Error: Railway CLI not found. Install it in the base image or supply PATH." >&2
    exit 2
fi

# Non-interactive auth: expect RAILWAY_TOKEN to be preset
if ! railway whoami &> /dev/null; then
    if [ -z "${RAILWAY_TOKEN:-}" ]; then
        echo "Error: Railway CLI not logged in and RAILWAY_TOKEN not provided for headless auth." >&2
        exit 3
    fi
    echo "$RAILWAY_TOKEN" | railway login --token -
fi
# ログディレクトリを作成
mkdir -p "$PROJECT_ROOT/railway/logs"

# ログ監視スクリプトを実行
echo "Starting log monitoring..."
cd "$PROJECT_ROOT"
python3 railway/scripts/log_monitor.py "$@" 