# **`priceComparisonAppForIphone`リポジトリについて**

# Claude や ChatGPT にリポジトリを丸ごと読み込ませるコマンド

以下のコマンドを実行することでリポジトリ一式をテキストファイル（`repomix-output.txt`, 旧：`repopack-output.txt`）を出力することができます。

```
npx repomix
// 2024/12/20 `repopack`からupgrade
```

chat へ最初に取り込ませることでコード修正に役立ちます。

### 読み込ませるポイント

ファイルと合わせて以下のプロンプトで始めるとスムーズに改修を始めやすい

```
このファイルはリポジトリのファイルを1つにしたものです。コードのリファクタなどをしたいのでまず添付のコードを確認してください。
```

# About setting to "Renovate"

## 説明:

- extends: ["config:base"]: デフォルト設定に基づきます。
- labels: ["dependencies"]: すべての PR に "dependencies" ラベルが付与されます。
- packageRules:
  - minor と patch の自動マージ: 自動的に PR がマージされます（automergeType: "pr"）。
  - 大規模なマイナー変更（特定のパッケージ）やメジャーアップデートは自動マージされません\*\*。
- prConcurrentLimit: 一度に開かれる PR の上限(number)。

この設定で、メジャーアップデートと大規模なマイナー変更は手動でマージすることができ、それ以外の更新は自動的にマージされます。

# `AWS`の設定について

## credentials について

以下`~/.aws/credentials`のサンプルになります(2024/12/20 時点のもの。セキュリティ面から 2,3 週間ごとに変更予定のため流用はほぼ不可)

```
[default]
aws_access_key_id = ********************
aws_secret_access_key = ****************************************
# 格納方法は別途検討中
```

※ MFA を有効にする場合、`aws cli`は追加対応が必要になるため注意が必要（AI に聞くなり「aws-cli mfa」などで調べてください。大体は「一時的なアクセス情報を発行する」や`aws sts`コマンドに行き着くかと思います）

※ `aws configure` は `--profile`オプションを追加して名前つきのプロファイルを設定することができます（上記同様 AI に聞くなりして調べてください）

## config について

以下`~/.aws/config`のサンプルになります。こちらは管理者が日本以外に帰化しない限りは以下のままかと思います。

```
[default]
region = ap-northeast-1
output = json
# outputについて、`yaml`等が良ければ必要に応じて変更してください
```

## DynamoDB create command

上記`aws configure`の設定は前提

```
aws dynamodb create-table \
  --table-name official_prices \
  --attribute-definitions \
      AttributeName=series,AttributeType=S \
      AttributeName=capacity,AttributeType=S \
  --key-schema \
      AttributeName=series,KeyType=HASH \
      AttributeName=capacity,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST
```

実際に保存したい情報（`2024/12/20`時点のもの）は`data/official_prices.json`に残っていたりもする（以前は`json`ファイルから描写していた名残）

## ディレクトリ構成について（`2024/12/20`時点）

```
priceComparisonAppForIphone/
│
├── scripts/  # スクリプト関連
│   ├── migrate_to_dynamodb.py  # データ移行用
│
├── services/  # AWSサービスごとの処理
│   ├── dynamodb_service.py  # DynamoDB操作
│   ├── lambda_handler.py  # Lambda関数のエントリーポイント
│
├── templates/  # HTMLテンプレート
│   ├── index.html  # フロントエンド
│
├── app.py  # Flaskサーバー
├── requirements.txt
└── README.md
```

# ローカル環境での実行手順

1. まず、必要な環境変数を設定します。`.env.example`をコピーして`.env`ファイルを作成：

```bash
cp .env.example .env
```

2. 必要な Python パッケージをインストール：

```bash
pip install -r requirements.txt
```

3. Playwright のブラウザをインストール：

```bash
playwright install chromium
```

4. アプリケーションの実行：

開発モード（デバッグ有効）での実行：

```bash
python app.py
```

または、本番モードでの実行（Gunicorn を使用）：

```bash
gunicorn app:app --bind 0.0.0.0:5000 --workers=3 --timeout=60
```

Docker を使用する場合：

```bash
# イメージのビルド
docker build -t price-comparison-app:latest .

# コンテナの実行
docker run -p 5000:5000 price-comparison-app:latest
```

アプリケーションが起動したら、ブラウザで以下の URL にアクセスできます：

```
http://localhost:5000
```

注意点：

- AWS 関連の機能を使用する場合は、AWS 認証情報の設定が必要です
- DynamoDB を使用する場合は、`~/.aws/credentials`の設定が必要です
- 開発環境では`config/config.development.yaml`の設定が使用されます

エラーが発生した場合は、ログを確認することで詳細な情報を得ることができます。
