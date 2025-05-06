# スクリプト使用方法

このディレクトリには、AWS リソースのデプロイメント、検証、クリーンアップに使用するスクリプトが含まれています。

## 前提条件

以下の環境変数が設定されている必要があります：

```bash
export AWS_ACCESS_KEY_ID="your_access_key"
export AWS_SECRET_ACCESS_KEY="your_secret_key"
export AWS_DEFAULT_REGION="your_region"
```

## スクリプト一覧

### 1. デプロイメントスクリプト (`deploy.py`)

AWS リソースのデプロイメントを実行します。

```bash
python3 deploy.py
```

実行手順：

1. Lambda 関数のパッケージング
2. Terraform の実行
3. デプロイメントの検証

### 2. デプロイメント検証スクリプト (`deployment-verification.py`)

デプロイされたリソースの状態を確認します。

```bash
python3 deployment-verification.py
```

検証内容：

1. Lambda 関数の状態確認
2. DynamoDB テーブルの状態確認
3. API Gateway の状態確認

### 3. クリーンアップスクリプト (`cleanup.py`)

AWS リソースのクリーンアップを実行します。

```bash
python3 cleanup.py
```

クリーンアップ手順：

1. DynamoDB テーブルのデータ削除
2. Terraform によるリソースの削除
3. クリーンアップの検証

### 4. Lambda 関数パッケージングスクリプト (`package_lambda.py`)

Lambda 関数をパッケージングします。

```bash
python3 package_lambda.py
```

### 5. データロードスクリプト (`load_dynamodb_data.py`)

DynamoDB テーブルにデータをロードします。

```bash
python3 load_dynamodb_data.py
```

### 6. スモークテストスクリプト (`smoke-test.py`)

デプロイされたリソースの基本的な機能テストを実行します。

```bash
python3 smoke-test.py
```

## エラーハンドリング

各スクリプトは以下のエラー処理を行います：

1. 環境変数の不足
2. AWS 認証エラー
3. リソースの存在確認
4. 操作の成功/失敗の検証

エラーが発生した場合は、ログに詳細な情報が出力されます。

## ログ出力

すべてのスクリプトは、以下の情報をログに出力します：

1. 実行開始/終了
2. 各ステップの進行状況
3. エラー情報
4. 検証結果

## 注意事項

1. クリーンアップスクリプトは、すべてのリソースを削除します。実行前に確認してください。
2. デプロイメントスクリプトは、既存のリソースを上書きします。
3. スモークテストは、実際の API エンドポイントを呼び出します。
