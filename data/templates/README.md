# Data Templates

このディレクトリには、API で取得できる形のデータテンプレートが含まれています。

## ファイル一覧

### `api_prices_template.json`

- **用途**: メインの価格比較 API レスポンス形式
- **構造**:
  - `official_price`: 公式価格
  - `kaitori_price`: 買取価格
  - `price_diff`: 価格差
  - `rakuten_diff`: 楽天での価格差
  - `colors`: 色別の価格情報

### `price_history_template.json`

- **用途**: 価格履歴データ
- **構造**:
  - `prices`: 時系列の価格データ
  - `latest_price`: 最新価格
  - `price_trend`: 価格トレンド（up/down/stable）
  - `price_change`: 価格変動

### `price_predictions_template.json`

- **用途**: 価格予測データ
- **構造**:
  - `predictions`: 予測履歴
  - `latest_prediction`: 最新予測
  - `confidence`: 予測信頼度
  - `factors`: 予測に使用した要因

## 使用方法

これらのテンプレートを基に、実際のデータを生成・更新してください。
API レスポンスの形式を統一し、フロントエンドでの処理を簡素化します。
