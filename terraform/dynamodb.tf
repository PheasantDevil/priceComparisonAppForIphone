# DynamoDBテーブルのデータ管理
resource "aws_dynamodb_table_item" "iphone_prices_data" {
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

  tags = {
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

  tags = {
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
  for_each = local.flattened_prices

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
          N = tostring(price)
        }
      }
    }
  })
} 