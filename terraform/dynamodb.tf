# DynamoDBテーブルのデータ管理
resource "aws_dynamodb_table_item" "iphone_prices_data" {
  count = var.create_sample_data ? 1 : 0

  table_name = aws_dynamodb_table.iphone_prices.name
  hash_key   = "series"
  range_key  = "capacity"

  item = jsonencode({
    series = {
      S = "iPhone 16"
    }
    capacity = {
      S = "128GB"
    }
    price = {
      N = "999"
    }
    timestamp = {
      S = timestamp()
    }
  })
}

# DynamoDBテーブルの定義
resource "aws_dynamodb_table" "iphone_prices" {
  name           = "iphone_prices"
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
    # prevent_destroy = true  # 一時的に無効化
  }

  tags = {
    Name        = "iphone_prices"
    Environment = "production"
    Project     = "iphone_price_tracker"
  }
}

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
    # prevent_destroy = true  # 一時的に無効化
  }

  tags = {
    Name        = "official_prices"
    Environment = "production"
    Project     = "iphone_price_tracker"
  }
}

# 価格情報を格納するメインテーブル
resource "aws_dynamodb_table" "price_comparison" {
  name           = "price-comparison"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "id"
  stream_enabled = true
  stream_view_type = "NEW_AND_OLD_IMAGES"

  attribute {
    name = "id"
    type = "S"
  }

  server_side_encryption {
    enabled = true
    kms_key_arn = aws_kms_key.data_encryption.arn
  }

  replica {
    region_name = "ap-southeast-1"
    kms_key_arn = aws_kms_key.data_encryption_replica.arn
  }

  tags = {
    Name        = "price-comparison"
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
    # prevent_destroy = true  # 一時的に無効化
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
    # prevent_destroy = true  # 一時的に無効化
  }

  tags = {
    Name        = "price_predictions"
    Environment = "production"
    Project     = "iphone_price_tracker"
  }
}