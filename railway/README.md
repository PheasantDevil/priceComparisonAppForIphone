# Railway Utilities

Railway のログ監視と Slack 通知機能を提供するユーティリティパッケージです。

## 機能

- Railway CLI を使用したログ取得
- Slack Incoming Webhook を使用した通知
- ログレベルのフィルタリング
- 重要なキーワードによる通知判定
- ヘルスチェック機能
- 設定の環境変数管理

## ディレクトリ構造

```
railway/
├── config/
│   ├── __init__.py
│   └── settings.py          # 設定管理
├── utils/
│   ├── __init__.py
│   ├── railway_client.py    # Railway CLIクライアント
│   └── slack_notifier.py    # Slack通知機能
├── scripts/
│   ├── __init__.py
│   ├── log_monitor.py       # メイン監視スクリプト
│   └── start_monitor.sh     # 実行用シェルスクリプト
├── examples/
│   └── usage_example.py     # 使用例
├── logs/                    # ログファイル
├── __init__.py
└── README.md
```

## セットアップ

### 1. 環境変数の設定

以下の環境変数を設定してください：

```bash
# Railway設定
export RAILWAY_PROJECT_ID="your-project-id"
export RAILWAY_SERVICE_ID="your-service-id"  # オプション
export RAILWAY_ENVIRONMENT="production"

# Slack設定
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
export SLACK_CHANNEL="#alerts"
export SLACK_USERNAME="Railway Log Monitor"
export SLACK_ICON_EMOJI=":railway_track:"

# ログ監視設定
export LOG_MONITOR_INTERVAL="60"
export LOG_MONITOR_MAX_LOGS="100"
export LOG_MONITOR_KEYWORDS="error,failed,timeout"
export LOG_MONITOR_LEVELS="ERROR,WARN,CRITICAL"
```

### 2. Railway CLI のインストール

```bash
npm install -g @railway/cli
```

### 3. 依存関係のインストール

```bash
pip install requests
```

## 使用方法

### 1. ログ監視の開始

```bash
# 継続監視
./railway/scripts/start_monitor.sh

# 単発実行（GitHub Actions用）
python railway/scripts/log_monitor.py --single-run

# ヘルスチェックのみ
python railway/scripts/log_monitor.py --health-check
```

### 2. 既存アプリケーションからの利用

```python
import sys
sys.path.append('.')

from railway import RailwayClient, SlackNotifier, validate_configs

# 設定の妥当性を検証
if not validate_configs():
    print("Configuration validation failed")
    exit(1)

# Railwayクライアントを作成
railway_client = RailwayClient()

# ログを取得
logs = railway_client.get_logs(limit=10)

# Slack通知を作成
slack_notifier = SlackNotifier()

# 通知を送信
success = slack_notifier.send_message("Hello from Railway!", "INFO")
```

### 3. カスタム通知の送信

```python
from railway import SlackNotifier

slack_notifier = SlackNotifier()

# ヘルスチェック通知
slack_notifier.send_health_check('healthy', {
    'project': 'My App',
    'services': 3,
    'environment': 'production'
})

# カスタムメッセージ
slack_notifier.send_message(
    "🚀 Deployment completed!",
    "INFO",
    attachments=[{
        "color": "#36a64f",
        "title": "Deployment Status",
        "text": "Successfully deployed to Railway"
    }]
)
```

## 設定オプション

### RailwayConfig

- `project_id`: Railway プロジェクト ID（必須）
- `service_id`: Railway サービス ID（オプション）
- `environment`: 環境名（デフォルト: "production"）

### SlackConfig

- `webhook_url`: Slack Incoming Webhook URL（必須）
- `channel`: 通知先チャンネル（デフォルト: "#general"）
- `username`: 通知ユーザー名（デフォルト: "Railway Log Monitor"）
- `icon_emoji`: アイコン絵文字（デフォルト: ":railway_track:"）

### LogMonitorConfig

- `interval`: 監視間隔（秒）（デフォルト: 60）
- `max_logs_per_batch`: 一度に取得する最大ログ数（デフォルト: 100）
- `important_keywords`: 重要なキーワードリスト
- `log_levels`: 通知するログレベルリスト

## ログレベルと色

- `INFO`: 緑 (#36a64f)
- `WARNING/WARN`: オレンジ (#ff9500)
- `ERROR`: 赤 (#ff0000)
- `CRITICAL`: 濃い赤 (#8b0000)

## トラブルシューティング

### Railway CLI エラー

```bash
# CLIのバージョンを確認
railway --version

# ログイン状態を確認
railway whoami

# 必要に応じてログイン
railway login
```

### Slack 通知エラー

- Webhook URL が正しいか確認
- チャンネル名が正しいか確認（例: "#alerts"）
- ネットワーク接続を確認

### 設定エラー

```bash
# 設定の妥当性を確認
python railway/examples/usage_example.py
```

## 開発

### テスト実行

```bash
# 使用例を実行
python railway/examples/usage_example.py

# ログ監視をテスト
python railway/scripts/log_monitor.py --single-run --log-level DEBUG
```

### ログの確認

```bash
# 監視ログを確認
tail -f railway/logs/monitor.log
```

## ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。
