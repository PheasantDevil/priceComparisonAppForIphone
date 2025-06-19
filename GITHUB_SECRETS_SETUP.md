# GitHub Secrets 設定ガイド

## 概要

GitHub Actions で App Engine Standard にデプロイするために必要な Secrets の設定方法を説明します。

## 必要な Secrets

### 1. `GCP_PROJECT_ID`

- **値**: Google Cloud Platform のプロジェクト ID
- **例**: `my-project-123456`
- **取得方法**: GCP コンソールの右上に表示されるプロジェクト ID

### 2. `GCP_SA_KEY`

- **値**: サービスアカウントの JSON キー全体
- **形式**: `{"type": "service_account", "project_id": "...", ...}`
- **取得方法**: 下記の手順で作成

## サービスアカウントの作成手順

### 1. Google Cloud SDK でサービスアカウントを作成

```bash
# プロジェクトIDを設定
export PROJECT_ID="your-project-id"

# サービスアカウントを作成
gcloud iam service-accounts create price-comparison-app \
  --display-name="Price Comparison App Service Account"

# 必要な権限を付与
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:price-comparison-app@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:price-comparison-app@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:price-comparison-app@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/appengine.deployer"

# キーを作成
gcloud iam service-accounts keys create key.json \
  --iam-account=price-comparison-app@$PROJECT_ID.iam.gserviceaccount.com

# JSONキーの内容を表示（これをGitHub Secretsに設定）
cat key.json
```

### 2. GitHub Secrets に設定

1. **GitHub リポジトリ** → **Settings** → **Secrets and variables** → **Actions**
2. **New repository secret** をクリック
3. 以下の 2 つの Secrets を作成：

#### `GCP_PROJECT_ID`

- **Name**: `GCP_PROJECT_ID`
- **Value**: あなたのプロジェクト ID（例: `my-project-123456`）

#### `GCP_SA_KEY`

- **Name**: `GCP_SA_KEY`
- **Value**: `cat key.json` で表示された JSON 全体

## 設定例

### GCP_PROJECT_ID

```
my-awesome-project-123456
```

### GCP_SA_KEY

```json
{
  "type": "service_account",
  "project_id": "my-awesome-project-123456",
  "private_key_id": "abc123...",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...\n-----END PRIVATE KEY-----\n",
  "client_email": "price-comparison-app@my-awesome-project-123456.iam.gserviceaccount.com",
  "client_id": "123456789",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/price-comparison-app%40my-awesome-project-123456.iam.gserviceaccount.com"
}
```

## トラブルシューティング

### よくあるエラー

1. **"Invalid grant: account not found"**

   - サービスアカウントが正しく作成されていない
   - JSON キーが正しくない
   - 解決策: 上記の手順でサービスアカウントを再作成

2. **"Permission denied"**

   - サービスアカウントに必要な権限が付与されていない
   - 解決策: 権限を再付与

3. **"Project not found"**
   - プロジェクト ID が間違っている
   - 解決策: 正しいプロジェクト ID を確認

## 確認方法

### 1. サービスアカウントの確認

```bash
gcloud iam service-accounts list
```

### 2. 権限の確認

```bash
gcloud projects get-iam-policy $PROJECT_ID
```

### 3. キーの確認

```bash
gcloud iam service-accounts keys list \
  --iam-account=price-comparison-app@$PROJECT_ID.iam.gserviceaccount.com
```

## セキュリティ注意事項

- **JSON キーは絶対に公開しないでください**
- **GitHub Secrets でのみ管理してください**
- **定期的にキーをローテーションしてください**
