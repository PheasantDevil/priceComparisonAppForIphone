# Data Templates

このディレクトリには、API で取得できる形のデータテンプレートが含まれています。
各ファイルは、フロントエンドでの処理を簡素化するための統一されたデータ構造を定義しています。

## ファイル一覧

### `api_prices.json`

- **用途**: メインの価格比較 API レスポンス形式
- **エンドポイント**: `/api/prices?series={series}`
- **構造**:
  - `official_price`: 公式価格（容量別の基本価格）
  - `kaitori_price`: 買取価格（容量別の基本価格）
  - `price_diff`: 価格差（公式価格 - 買取価格）
  - `rakuten_diff`: 楽天での価格差
  - `colors`: 色別の公式価格（直接価格値を保存）
- **対象モデル**: iPhone 16, iPhone 16 Plus, iPhone 16 Pro, iPhone 16 Pro Max, iPhone 16e
- **容量**: 128GB, 256GB, 512GB, 1TB（モデルにより異なる）

### `official_prices.json`

- **用途**: 公式価格データの基本テンプレート
- **構造**:
  - `colors`: 色別の公式価格のみ
  - シンプルな構造で公式価格のみを管理
- **特徴**:
  - 買取価格や価格差を含まない純粋な公式価格データ
  - 他のデータソースとの比較基準として使用
- **対象モデル**: iPhone 16, iPhone 16 Plus, iPhone 16 Pro, iPhone 16 Pro Max, iPhone 16e

### `price_history.json`

- **用途**: 価格履歴データのテンプレート
- **構造**:
  - `series`: モデル名
  - `capacity`: 容量
  - `color`: 色
  - `prices`: 時系列の価格データ配列
    - `timestamp`: Unix タイムスタンプ
    - `date`: 日付（YYYY-MM-DD 形式）
    - `price`: 買取価格
    - `source`: データソース
    - `official_price`: 公式価格
    - `price_diff`: 価格差
  - `latest_price`: 最新価格
  - `price_trend`: 価格トレンド（up/down/stable）
  - `price_change`: 価格変動額
- **キー形式**: `{モデル}-{容量}-{色}`（例: iPhone 16-128GB-Black）

### `price_predictions.json`

- **用途**: 価格予測データのテンプレート
- **構造**:
  - `predictions`: 予測履歴配列
    - `timestamp`: Unix タイムスタンプ
    - `date`: 日付（YYYY-MM-DD 形式）
    - `predicted_price`: 予測価格
    - `confidence`: 予測信頼度（0.0-1.0）
    - `factors`: 予測に使用した要因
      - `market_trend`: 市場トレンド
      - `seasonal_factor`: 季節要因
      - `model_age`: モデル年齢
      - `demand_level`: 需要レベル
    - `prediction_horizon`: 予測期間
    - `algorithm`: 使用アルゴリズム
  - `latest_prediction`: 最新予測
    - `price`: 予測価格
    - `confidence`: 信頼度
    - `trend`: トレンド（up/down/stable）
    - `change`: 価格変動予測

## データ形式の統一

### 色別価格の保存形式

```json
"colors": {
  "Black": 124800,
  "White": 124800,
  "Blue": 124800,
  "Green": 124800
}
```

- 色名をキーとして、直接価格値を保存
- 公式価格データと同じ形式
- シンプルで扱いやすい構造

### 価格データの単位

- すべての価格は**円**で統一
- 負の値は価格差（公式価格 - 買取価格）を表す

### 日付・時刻形式

- `timestamp`: Unix タイムスタンプ（秒）
- `date`: ISO 8601 形式（YYYY-MM-DD）

## 使用方法

### 1. テンプレートの活用

これらのテンプレートを基に、実際のデータを生成・更新してください。

### 2. API レスポンスの統一

フロントエンドでの処理を簡素化するため、API レスポンスの形式を統一します。

### 3. データ更新時の注意点

- 価格データ更新時は、関連する`price_diff`も同時に更新
- 履歴データは時系列順に管理
- 予測データは信頼度と共に管理

### 4. 拡張時のガイドライン

- 新しいモデル追加時は、既存の構造に合わせる
- 新しいフィールド追加時は、後方互換性を考慮
- データ型は一貫性を保つ

## ファイル命名規則

- `api_*.json`: API レスポンス用テンプレート
- `*_prices.json`: 価格データ関連
- `price_*.json`: 価格分析関連（履歴、予測など）
- `official_*.json`: 公式データ関連
