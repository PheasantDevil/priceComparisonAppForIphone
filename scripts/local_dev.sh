#!/bin/bash

# スクリプトのディレクトリを取得
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# プロジェクトのルートディレクトリに移動
cd "$PROJECT_ROOT"

# 必要なディレクトリの作成
echo "必要なディレクトリを作成中..."
mkdir -p logs
mkdir -p cache
mkdir -p config
mkdir -p src/lambda_functions/get_prices_lambda

# 仮想環境の作成と有効化
echo "仮想環境を作成中..."
python3 -m venv venv
source venv/bin/activate

# 依存関係のインストール
echo "依存関係をインストール中..."
pip install -r requirements.txt
pip install requests beautifulsoup4 boto3 pyyaml pytest pytest-cov

# ローカル開発用の設定ファイルを作成
echo "ローカル開発用の設定ファイルを作成中..."
cat > config/local_config.yaml << EOL
scraper:
  user_agent: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
  request_timeout: 10
  kaitori_rudea_urls:
    - "https://example.com/kaitori1"
    - "https://example.com/kaitori2"
  apple_store_url: "https://example.com/apple"
  cache:
    enabled: true
    duration: 3600
    directory: "cache"

dynamodb:
  region: "ap-northeast-1"
  table_name: "iphone_prices"
  endpoint_url: "http://localhost:8000"  # DynamoDB Localを使用する場合
EOL

# テストの実行
echo "テストを実行中..."
export PYTHONPATH=$PROJECT_ROOT
pytest tests/ --cov=src --cov-report=term-missing

# ローカル開発用のDynamoDB Localのセットアップ（オプション）
echo "DynamoDB Localのセットアップ（オプション）..."
if [ ! -f "dynamodb_local_latest.tar.gz" ]; then
    echo "DynamoDB Localをダウンロード中..."
    curl -L -o dynamodb_local_latest.tar.gz https://s3.us-west-2.amazonaws.com/dynamodb-local/dynamodb_local_latest.tar.gz
    mkdir -p dynamodb_local
    tar xf dynamodb_local_latest.tar.gz -C dynamodb_local
fi

# 開発用のヘルパースクリプトを作成
echo "開発用のヘルパースクリプトを作成中..."
cat > scripts/run_local.sh << EOL
#!/bin/bash
source venv/bin/activate
export PYTHONPATH=\$(pwd)
python src/lambda_functions/get_prices_lambda/scraper.py
EOL
chmod +x scripts/run_local.sh

echo "ローカル開発環境のセットアップが完了しました！"
echo "以下のコマンドで開発を開始できます："
echo "1. 仮想環境の有効化: source venv/bin/activate"
echo "2. スクレイパーの実行: ./scripts/run_local.sh"
echo "3. テストの実行: PYTHONPATH=\$(pwd) pytest tests/" 