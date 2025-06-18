# Scripts Directory

このディレクトリには、GCP 環境での価格比較アプリケーションの管理に使用するスクリプトが含まれています。

## 前提条件

以下の環境変数が設定されている必要があります：

```bash
export GOOGLE_APPLICATION_CREDENTIALS="path/to/key.json"
export BUCKET_NAME="price-comparison-app-data"
```

## スクリプト一覧

### データ管理スクリプト

#### 1. Cloud Storage → Firestore 同期 (`sync_cloud_storage_to_firestore.py`)

Cloud Storage の最新スクレイピングデータを Firestore に同期します。

```bash
python scripts/sync_cloud_storage_to_firestore.py
```

**機能:**

- Cloud Storage から最新の価格データを取得
- Firestore の`kaitori_prices`コレクションを更新
- `price_history`コレクションに履歴データを保存
- 容量の正規化（1GB → 1TB）

#### 2. 公式価格リセット (`reset_and_reload_official_prices.py`)

Firestore の公式価格データをリセットして再投入します。

```bash
python scripts/reset_and_reload_official_prices.py
```

#### 3. 買取価格リセット (`reset_and_reload_kaitori_prices.py`)

Firestore の買取価格データをリセットして再投入します。

```bash
python scripts/reset_and_reload_kaitori_prices.py
```

#### 4. 価格データ追加 (`add_iphone_prices.py`)

Firestore に iPhone 価格データを追加します。

```bash
python scripts/add_iphone_prices.py
```

#### 5. 買取価格エクスポート (`export_kaitori_prices.py`)

Firestore の買取価格データを JSON ファイルにエクスポートします。

```bash
python scripts/export_kaitori_prices.py
```

### デプロイメントスクリプト

#### 1. Cloud Function デプロイ (`deploy_cloud_function.sh`)

Cloud Function をデプロイします。

```bash
bash scripts/deploy_cloud_function.sh
```

#### 2. Cloud Run デプロイ (`deploy_cloud_run.sh`)

Cloud Run サービスをデプロイします。

```bash
bash scripts/deploy_cloud_run.sh
```

## 使用方法

### 1. 初回セットアップ

```bash
# 公式価格データの設定
python scripts/add_iphone_prices.py

# Cloud StorageからFirestoreへの同期
python scripts/sync_cloud_storage_to_firestore.py
```

### 2. 定期実行

GitHub Actions ワークフロー（`.github/workflows/scrape_prices.yml`）で自動実行されます：

- 毎日 10 時と 22 時にスクレイピング実行
- スクレイピング後に自動的に Firestore に同期

### 3. 手動実行

```bash
# データの同期
python scripts/sync_cloud_storage_to_firestore.py

# 価格データのリセット
python scripts/reset_and_reload_kaitori_prices.py
python scripts/reset_and_reload_official_prices.py
```

## データ構造

### Firestore コレクション

#### `kaitori_prices`

買取価格の現在データ

```json
{
  "series": "iPhone 16 Pro",
  "capacity": "1TB",
  "kaitori_price_min": 223200,
  "kaitori_price_max": 223200,
  "colors": { "黒": 223200, "白": 223200 },
  "source": "kaitori-rudea",
  "updated_at": "2025-06-18T14:51:18.149"
}
```

#### `price_history`

価格履歴データ（グラフ化用）

```json
{
  "model": "iPhone 16 Pro_1TB",
  "timestamp": 1718705478,
  "series": "iPhone 16 Pro",
  "capacity": "1TB",
  "colors": { "黒": 223200, "白": 223200 },
  "kaitori_price_min": 223200,
  "kaitori_price_max": 223200,
  "source": "kaitori-rudea",
  "expiration_time": 1719910278
}
```

#### `official_prices`

公式価格データ

```json
{
  "iPhone 16 Pro": {
    "128GB": { "price": 145000 },
    "256GB": { "price": 161000 },
    "512GB": { "price": 189000 },
    "1TB": { "price": 223000 }
  }
}
```

## 注意事項

1. スクリプト実行前に`key.json`（GCP サービスアカウントキー）が配置されていることを確認してください
2. データリセットスクリプトは既存データを削除します。実行前に確認してください
3. 容量の正規化により、スクレイピングデータの`1GB`は`1TB`に変換されます

## エラーハンドリング

各スクリプトは以下のエラー処理を行います：

1. 認証情報の不足
2. GCP リソースへのアクセスエラー
3. データの整合性チェック
4. 操作の成功/失敗の検証

エラーが発生した場合は、ログに詳細な情報が出力されます。
