# 手動設定ガイド

## サービスアカウント権限の設定

GitHub Actions ワークフローで Firestore にアクセスするために、サービスアカウントに適切な権限を手動で設定する必要があります。

### 前提条件

- Google Cloud Console にアクセスできる管理者権限
- `gcloud` CLI がインストールされている

### 手順

1. **Google Cloud Console にログイン**

   ```bash
   gcloud auth login
   ```

2. **プロジェクトを設定**

   ```bash
   gcloud config set project price-comparison-app-463007
   ```

3. **サービスアカウントに Firestore 権限を付与**

   ```bash
   # Firestoreユーザー権限
   gcloud projects add-iam-policy-binding price-comparison-app-463007 \
     --member="serviceAccount:price-comparison-app@price-comparison-app-463007.iam.gserviceaccount.com" \
     --role="roles/datastore.user"

   # Firestore管理者権限（セキュリティルールのデプロイ用）
   gcloud projects add-iam-policy-binding price-comparison-app-463007 \
     --member="serviceAccount:price-comparison-app@price-comparison-app-463007.iam.gserviceaccount.com" \
     --role="roles/datastore.owner"
   ```

4. **権限の確認**
   ```bash
   gcloud projects get-iam-policy price-comparison-app-463007 \
     --flatten="bindings[].members" \
     --format="table(bindings.role)" \
     --filter="bindings.members:price-comparison-app@price-comparison-app-463007.iam.gserviceaccount.com"
   ```

### 期待される出力

```
ROLE
roles/datastore.user
roles/datastore.owner
```

### Firestore セキュリティルールの手動デプロイ（オプション）

ワークフローでエラーが発生した場合、手動でデプロイできます：

```bash
# gcloud CLIでFirestoreルールをデプロイ
gcloud firestore rules deploy functions/firestore.rules \
  --project=price-comparison-app-463007
```

### トラブルシューティング

**エラー: "does not have permission to access projects instance"**

- 管理者権限を持つアカウントでログインしていることを確認
- プロジェクト ID が正しいことを確認

**エラー: "service account does not exist"**

- サービスアカウント名が正しいことを確認
- サービスアカウントが作成されていることを確認

**エラー: "gcloud firestore rules command not found"**

- Google Cloud SDK が最新版であることを確認
- `gcloud components update`を実行

### セキュリティ注意事項

- 本番環境では必要最小限の権限のみを付与
- 定期的に権限の見直しを行う
- サービスアカウントキーは安全に管理
