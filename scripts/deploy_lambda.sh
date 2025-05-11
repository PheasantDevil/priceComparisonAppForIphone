<<COMMENT 
# ディレクトリ構造
project/
├── src/
│   ├── apple_scraper_for_rudea.py
│   └── apple_scraper.py
├── services/
│   └── dynamodb_service.py
├── lambda/
│   ├── get_prices_lambda.py
│   └── lambda_handler.py
├── scripts/
│   └── deploy_lambda.sh
├── artifacts/
│   └── lambda/
│       ├── function_20240318_123456.zip
│       ├── function_20240318_234567.zip
│       └── function_latest.zip -> function_20240318_234567.zip
└── requirements.txt

# デプロイスクリプト

## デプロイパッケージを作成してアップロード
./scripts/deploy_lambda.sh

COMMENT

#!/bin/bash

# スクリプトのディレクトリを取得
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# プロジェクトのルートディレクトリに移動
cd "$PROJECT_ROOT"

# デプロイパッケージの保存ディレクトリ
ARTIFACTS_DIR="artifacts/lambda"
mkdir -p $ARTIFACTS_DIR

# タイムスタンプ付きのファイル名を生成
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
FUNCTION_ZIP="function_${TIMESTAMP}.zip"
FUNCTION_PATH="$ARTIFACTS_DIR/$FUNCTION_ZIP"

# デプロイ用の一時ディレクトリを作成
DEPLOY_DIR="deploy_tmp"
rm -rf $DEPLOY_DIR
mkdir -p $DEPLOY_DIR

echo "必要なファイルをコピー中..."
# Lambda関数のコードをコピー
cp lambdas/get_prices_lambda/lambda_function.py $DEPLOY_DIR/lambda_function.py
cp -r src $DEPLOY_DIR/
cp -r services $DEPLOY_DIR/
cp -r config $DEPLOY_DIR/  # 設定ファイルをコピー

echo "依存関係をインストール中..."
# 依存関係をインストール
pip3 install requests beautifulsoup4 boto3 pyyaml -t $DEPLOY_DIR/

echo "デプロイパッケージを作成中..."
# デプロイパッケージを作成
cd $DEPLOY_DIR
zip -r ../$FUNCTION_PATH .

# プロジェクトルートに戻る
cd "$PROJECT_ROOT"

# 一時ディレクトリを削除
rm -rf $DEPLOY_DIR

echo "デプロイパッケージ $FUNCTION_PATH が作成されました"

# 最新のzipファイルへのシンボリックリンクを作成
cd $ARTIFACTS_DIR
ln -sf $FUNCTION_ZIP function_latest.zip
cd "$PROJECT_ROOT"

echo "シンボリックリンク $ARTIFACTS_DIR/function_latest.zip が更新されました"

# IAMロールの作成（存在しない場合）
aws iam create-role \
    --role-name get_prices_lambda_role \
    --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }]
    }' || true

# DynamoDB アクセス権限の追加
aws iam put-role-policy \
    --role-name get_prices_lambda_role \
    --policy-name dynamodb-access \
    --policy-document '{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetItem",
                "dynamodb:Query"
            ],
            "Resource": "arn:aws:dynamodb:ap-northeast-1:*:table/iphone_prices"
        }]
    }' || true

# CloudWatch Logs アクセス権限の追加
aws iam attach-role-policy \
    --role-name get_prices_lambda_role \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole || true

# Lambda関数の更新
aws lambda update-function-code \
    --function-name get_prices \
    --zip-file fileb://$ARTIFACTS_DIR/function_latest.zip

# Lambda関数の設定更新
aws lambda update-function-configuration \
    --function-name get_prices \
    --handler lambda_function.lambda_handler \
    --role "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/get_prices_lambda_role" \
    --timeout 30 \
    --memory-size 256

echo "Lambda関数が更新されました"

# DynamoDBテーブルの作成（存在しない場合）
# 公式価格テーブル
aws dynamodb create-table \
    --table-name official_prices \
    --attribute-definitions \
        AttributeName=series,AttributeType=S \
    --key-schema \
        AttributeName=series,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST || true

# 買取価格テーブル
aws dynamodb create-table \
    --table-name kaitori_prices \
    --attribute-definitions \
        AttributeName=series,AttributeType=S \
    --key-schema \
        AttributeName=series,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST || true

# テーブルが作成されるのを待機
aws dynamodb wait table-exists --table-name official_prices
aws dynamodb wait table-exists --table-name kaitori_prices

# サンプルデータの投入（公式価格）
aws dynamodb put-item \
    --table-name official_prices \
    --item '{
        "series": {"S": "iPhone 16"},
        "price": {"M": {
            "128GB": {"N": "124800"},
            "256GB": {"N": "139800"},
            "512GB": {"N": "169800"}
        }}
    }'

aws dynamodb put-item \
    --table-name official_prices \
    --item '{
        "series": {"S": "iPhone 16 Pro"},
        "price": {"M": {
            "128GB": {"N": "159800"},
            "256GB": {"N": "174800"},
            "512GB": {"N": "204800"},
            "1TB": {"N": "234800"}
        }}
    }'

aws dynamodb put-item \
    --table-name official_prices \
    --item '{
        "series": {"S": "iPhone 16 Pro Max"},
        "price": {"M": {
            "256GB": {"N": "189800"},
            "512GB": {"N": "219800"},
            "1TB": {"N": "249800"}
        }}
    }'

# サンプルデータの投入（買取価格）
aws dynamodb put-item \
    --table-name kaitori_prices \
    --item '{
        "series": {"S": "iPhone 16"},
        "price": {"M": {
            "128GB": {"N": "100000"},
            "256GB": {"N": "115000"},
            "512GB": {"N": "145000"}
        }}
    }'

aws dynamodb put-item \
    --table-name kaitori_prices \
    --item '{
        "series": {"S": "iPhone 16 Pro"},
        "price": {"M": {
            "128GB": {"N": "135000"},
            "256GB": {"N": "150000"},
            "512GB": {"N": "180000"},
            "1TB": {"N": "210000"}
        }}
    }'

aws dynamodb put-item \
    --table-name kaitori_prices \
    --item '{
        "series": {"S": "iPhone 16 Pro Max"},
        "price": {"M": {
            "256GB": {"N": "165000"},
            "512GB": {"N": "195000"},
            "1TB": {"N": "225000"}
        }}
    }'