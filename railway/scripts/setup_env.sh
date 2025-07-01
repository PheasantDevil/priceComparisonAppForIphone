#!/bin/bash

# Railway環境変数設定スクリプト

echo "🚂 Railway Log Monitor 環境変数設定"
echo "=================================="

# 現在のディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "Project root: $PROJECT_ROOT"

# プロジェクトルートに移動
cd "$PROJECT_ROOT"

# 環境変数を設定
export RAILWAY_PROJECT_ID="4f0bf6cf-f794-41a9-9c8c-1f74bc38ab48"
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/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"
export SLACK_CHANNEL="#alerts"
export SLACK_USERNAME="Railway Log Monitor"
export SLACK_ICON_EMOJI=":steam_locomotive:"
export RAILWAY_ENVIRONMENT="production"
export LOG_MONITOR_INTERVAL="60"
export LOG_MONITOR_MAX_LOGS="100"
export LOG_MONITOR_KEYWORDS="error,failed,timeout,exception,critical"
export LOG_MONITOR_LEVELS="ERROR,WARN,CRITICAL"

echo "✅ 環境変数が設定されました"
echo ""
echo "設定内容:"
echo "  RAILWAY_PROJECT_ID: $RAILWAY_PROJECT_ID"
echo "  SLACK_WEBHOOK_URL: ${SLACK_WEBHOOK_URL:0:50}..."
echo "  SLACK_CHANNEL: $SLACK_CHANNEL"
echo "  SLACK_USERNAME: $SLACK_USERNAME"
echo "  SLACK_ICON_EMOJI: $SLACK_ICON_EMOJI"
echo "  RAILWAY_ENVIRONMENT: $RAILWAY_ENVIRONMENT"
echo "  LOG_MONITOR_INTERVAL: $LOG_MONITOR_INTERVAL"
echo ""

# 設定の妥当性を確認
echo "🔍 設定の妥当性を確認中..."

if python3 -c "
import sys
import os
sys.path.insert(0, os.getcwd())
from railway import validate_configs
if validate_configs():
    print('✅ 設定が正常です')
    exit(0)
else:
    print('❌ 設定に問題があります')
    exit(1)
"; then
    echo "✅ 設定の妥当性確認が完了しました"
    echo ""
    echo "🚀 ログ監視を開始するには以下を実行してください:"
    echo "  ./railway/scripts/start_monitor.sh"
    echo ""
    echo "または、単発実行の場合:"
    echo "  python3 railway/scripts/log_monitor.py --single-run"
    echo ""
    echo "テスト通知を送信する場合:"
    echo "  python3 railway/scripts/test_notification.py"
else
    echo "❌ 設定の妥当性確認に失敗しました"
    exit 1
fi 