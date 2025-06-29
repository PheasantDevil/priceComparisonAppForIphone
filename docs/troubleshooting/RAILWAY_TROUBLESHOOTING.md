# Railway トラブルシューティングガイド

## 🚨 よくあるエラーと解決策

### 1. "Service not found" エラー

#### 問題

```
Service not found
Multiple services found. Please specify a service via the `--service` flag.
```

#### 解決策

##### 手動でのサービス確認

1. Railway ダッシュボードにアクセス
2. プロジェクト `price-comparison-app` を選択
3. **"Settings"** タブでサービス名を確認
4. 通常は `web` または `price-comparison-app`

##### Railway CLI での確認

```bash
# プロジェクトにリンク
railway link

# サービス一覧を表示
railway service list

# 特定のサービスにリンク
railway service web
```

### 2. "No service could be found" エラー

#### 問題

```
No service could be found. Please either link one with `railway service` or specify one via the `--service` flag.
```

#### 解決策

##### プロジェクトの初期化

```bash
# Railway CLIにログイン
railway login

# プロジェクトにリンク
railway link

# サービスを選択
railway service
```

##### 手動でのサービス作成

1. Railway ダッシュボードで **"New Service"** をクリック
2. **"GitHub Repo"** を選択
3. リポジトリ `priceComparisonAppForIphone` を選択
4. サービス名を `web` に設定

### 3. "Service list not available" エラー

#### 問題

```
Service "list" not found.
Run `railway service` to connect to a service.
```

#### 解決策

##### Railway CLI の更新

```bash
# 最新版に更新
npm install -g @railway/cli@latest

# バージョン確認
railway --version
```

##### 認証の確認

```bash
# トークンでログイン
railway login --token YOUR_RAILWAY_TOKEN

# プロジェクトにリンク
railway link
```

### 4. デプロイ失敗の一般的な解決策

#### 4.1 環境変数の確認

Railway ダッシュボードで以下を確認：

- `APP_ENV=production`
- `SECRET_KEY=3C2jgeNUv6cfkksXVxiDuw1nI1WvCRxZYpUzeAZzsIIQ2uXh7UCSoTXYwNlRmThrdNRqN6cd0x4VYAQ-mF7lAg`
- `BUCKET_NAME=price-comparison-app-data`

#### 4.2 ポート設定の確認

Flask アプリが正しいポートを使用しているか確認：

```python
# app.py の最後の行
app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
```

#### 4.3 依存関係の確認

`requirements.txt` が正しく設定されているか確認：

```
Flask==3.1.1
gunicorn==22.0.0
google-cloud-storage==2.16.0
google-cloud-firestore==2.18.0
python-dotenv==1.1.0
tenacity==8.2.3
PyYAML==6.0.1
```

### 5. 手動でのデプロイ手順

#### 5.1 ローカルでのテスト

```bash
# 依存関係をインストール
pip install -r requirements.txt

# アプリを起動
python app.py
```

#### 5.2 Railway CLI での手動デプロイ

```bash
# Railway CLIをインストール
npm install -g @railway/cli@latest

# ログイン
railway login

# プロジェクトにリンク
railway link

# サービスを選択
railway service

# デプロイ
railway up
```

### 6. GitHub Actions でのデバッグ

#### 6.1 ワークフローの手動実行

1. GitHub リポジトリの **"Actions"** タブにアクセス
2. **"Deploy to Railway"** ワークフローを選択
3. **"Run workflow"** をクリック
4. デバッグ情報を確認

#### 6.2 ログの確認

```bash
# Railway ダッシュボードでログを確認
# または Railway CLIでログを取得
railway logs
```

### 7. プロジェクトの再初期化

#### 7.1 Railway プロジェクトの削除と再作成

1. Railway ダッシュボードでプロジェクトを削除
2. **"New Project"** をクリック
3. **"Deploy from GitHub repo"** を選択
4. リポジトリ `priceComparisonAppForIphone` を選択
5. サービス名を `web` に設定

#### 7.2 環境変数の再設定

新しいプロジェクトで環境変数を再設定：

- `APP_ENV=production`
- `SECRET_KEY=3C2jgeNUv6cfkksXVxiDuw1nI1WvCRxZYpUzeAZzsIIQ2uXh7UCSoTXYwNlRmThrdNRqN6cd0x4VYAQ-mF7lAg`
- `BUCKET_NAME=price-comparison-app-data`

### 8. 完了チェックリスト

- [ ] Railway CLI が最新版
- [ ] Railway Token が GitHub Secrets に設定済み
- [ ] プロジェクトが正しくリンクされている
- [ ] サービスが正しく選択されている
- [ ] 環境変数が設定済み
- [ ] 依存関係が正しくインストールされている
- [ ] ポート設定が正しい
- [ ] ヘルスチェックが成功している

### 9. サポート

問題が解決しない場合：

1. Railway ダッシュボードのログを確認
2. GitHub Actions のログを確認
3. Railway CLI のバージョンを確認
4. プロジェクトの再初期化を検討
