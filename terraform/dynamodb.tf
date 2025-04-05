# DynamoDBテーブルのデータ管理
resource "aws_dynamodb_table_item" "iphone_prices_data" {
  table_name = aws_dynamodb_table.iphone_prices.name
  hash_key   = aws_dynamodb_table.iphone_prices.hash_key
  range_key  = aws_dynamodb_table.iphone_prices.range_key

  item = jsonencode({
    id        = "initial_data"
    timestamp = timestamp()
    data      = {
      series   = "iPhone 16"
      capacity = "128GB"
      price    = 999
      store    = "Apple Store"
    }
  })
}

resource "aws_dynamodb_table_item" "official_prices_data" {
  table_name = aws_dynamodb_table.official_prices.name
  hash_key   = aws_dynamodb_table.official_prices.hash_key
  range_key  = aws_dynamodb_table.official_prices.range_key

  item = jsonencode({
    series   = "iPhone 16"
    capacity = "128GB"
    price    = 999
  })
} 