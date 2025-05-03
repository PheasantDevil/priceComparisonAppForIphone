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
  name         = "iphone_prices"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "series"
  range_key    = "capacity"

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
  name         = "official_prices"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "series"
  range_key    = "capacity"

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

# DynamoDBテーブルの設定

# 価格情報を格納するメインテーブル
resource "aws_dynamodb_table" "price_comparison" {
  name         = "price-comparison"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"
  range_key    = "timestamp"

  attribute {
    name = "id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  tags = {
    Name        = "price-comparison"
    Environment = var.environment
    Project     = var.project
  }
}

# DynamoDBのオートスケーリング設定
resource "aws_appautoscaling_target" "dynamodb_table_read_target" {
  max_capacity       = 50
  min_capacity       = 5
  resource_id        = "table/${aws_dynamodb_table.price_comparison.name}"
  scalable_dimension = "dynamodb:table:ReadCapacityUnits"
  service_namespace  = "dynamodb"
}

resource "aws_appautoscaling_policy" "dynamodb_table_read_policy" {
  name               = "dynamodb-read-capacity-scaling-policy"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.dynamodb_table_read_target.resource_id
  scalable_dimension = aws_appautoscaling_target.dynamodb_table_read_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.dynamodb_table_read_target.service_namespace

  target_tracking_scaling_policy_configuration {
    target_value       = 70.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 300

    predefined_metric_specification {
      predefined_metric_type = "DynamoDBReadCapacityUtilization"
    }
  }
}

resource "aws_appautoscaling_target" "dynamodb_table_write_target" {
  max_capacity       = 25
  min_capacity       = 5
  resource_id        = "table/${aws_dynamodb_table.price_comparison.name}"
  scalable_dimension = "dynamodb:table:WriteCapacityUnits"
  service_namespace  = "dynamodb"
}

resource "aws_appautoscaling_policy" "dynamodb_table_write_policy" {
  name               = "dynamodb-write-capacity-scaling-policy"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.dynamodb_table_write_target.resource_id
  scalable_dimension = aws_appautoscaling_target.dynamodb_table_write_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.dynamodb_table_write_target.service_namespace

  target_tracking_scaling_policy_configuration {
    target_value       = 70.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 300

    predefined_metric_specification {
      predefined_metric_type = "DynamoDBWriteCapacityUtilization"
    }
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

  table_name = aws_dynamodb_table.price_comparison.name
  hash_key   = "model"
  range_key  = "timestamp"

  item = jsonencode({
    model = {
      S = "${each.value.series} ${each.value.capacity}"
    }
    timestamp = {
      S = timestamp()
    }
    store = {
      S = "Apple"
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

resource "aws_dynamodb_table" "price_history" {
  name         = "price_history"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "model"
  range_key    = "timestamp"

  attribute {
    name = "model"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "N"  # 数値型に変更
  }

  attribute {
    name = "date"
    type = "S"  # 新しいGSI用の属性
  }

  ttl {
    attribute_name = "expiration_time"  # 属性名を変更
    enabled        = true
  }

  global_secondary_index {
    name            = "TimestampIndex"
    hash_key        = "model"
    range_key       = "timestamp"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "DateIndex"
    hash_key        = "date"
    range_key       = "model"
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