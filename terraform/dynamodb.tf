# DynamoDBテーブルのデータ管理

# DynamoDBテーブルの定義
resource "aws_dynamodb_table" "official_prices" {
  name           = "official_prices"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "series"
  range_key      = "capacity"

  attribute {
    name = "series"
    type = "S"
  }

  attribute {
    name = "capacity"
    type = "S"
  }

  global_secondary_index {
    name            = "CapacityIndex"
    hash_key        = "series"
    range_key       = "capacity"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  lifecycle {
    ignore_changes = [
      read_capacity,
      write_capacity,
      billing_mode
    ]
  }

  tags = {
    Name        = "official_prices"
    Environment = "production"
    Project     = "iphone_price_tracker"
  }
}

# 公式価格データの登録
locals {
  official_prices = jsondecode(file("${path.module}/../data/official_prices.json"))

  flattened_prices = {
    for item in flatten([
      for series, models in local.official_prices : [
        for capacity, colors in models : {
          series   = series
          capacity = capacity
          colors   = colors
        }
      ]
    ]) : "${item.series}-${item.capacity}" => item
  }
}

resource "aws_dynamodb_table_item" "official_prices_data" {
  for_each = var.create_sample_data ? local.flattened_prices : {}

  table_name = aws_dynamodb_table.official_prices.name
  hash_key   = "series"
  range_key  = "capacity"

  item = jsonencode({
    series = {
      S = each.value.series
    }
    capacity = {
      S = each.value.capacity
    }
    colors = {
      M = {
        for color, price in each.value.colors : color => {
          S = tostring(price)  # 数値を文字列として保存
        }
      }
    }
    timestamp = {
      S = timestamp()
    }
  })
}

resource "aws_dynamodb_table" "price_history" {
  name           = "price_history"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "model"
  range_key      = "timestamp"

  attribute {
    name = "model"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "N"
  }

  global_secondary_index {
    name            = "TimestampIndex"
    hash_key        = "model"
    range_key       = "timestamp"
    projection_type = "ALL"
  }

  ttl {
    attribute_name = "expiration_time"
    enabled        = true
  }

  lifecycle {
    ignore_changes = [
      read_capacity,
      write_capacity,
      billing_mode
    ]
  }

  tags = {
    Name        = "price_history"
    Environment = "production"
    Project     = "iphone_price_tracker"
  }
}

resource "aws_dynamodb_table" "price_predictions" {
  name           = "price_predictions"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "series"
  range_key      = "timestamp"

  attribute {
    name = "series"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  lifecycle {
    ignore_changes = [
      read_capacity,
      write_capacity,
      billing_mode
    ]
  }

  tags = {
    Name        = "price_predictions"
    Environment = "production"
    Project     = "iphone_price_tracker"
  }
}

resource "aws_dynamodb_table" "kaitori_prices" {
  name           = "kaitori_prices"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "id"

  attribute {
    name = "id"
    type = "S"
  }

  attribute {
    name = "price"
    type = "N"
  }

  global_secondary_index {
    name            = "PriceIndex"
    hash_key        = "id"
    range_key       = "price"
    projection_type = "ALL"
  }

  lifecycle {
    ignore_changes = [
      read_capacity,
      write_capacity,
      billing_mode
    ]
  }

  tags = {
    Name        = "kaitori_prices"
    Environment = "production"
    Project     = "iphone_price_tracker"
  }
}