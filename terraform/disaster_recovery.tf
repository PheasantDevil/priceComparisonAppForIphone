# プライマリテーブルを先に作成
# resource "aws_dynamodb_table" "price_comparison_primary" {
#   name           = "price-comparison"
#   billing_mode   = "PAY_PER_REQUEST"
#   hash_key       = "id"
#   range_key      = "timestamp"
# 
#   attribute {
#     name = "id"
#     type = "S"
#   }
# 
#   attribute {
#     name = "timestamp"
#     type = "S"
#   }
# 
#   tags = {
#     Name        = "price-comparison"
#     Environment = "production"
#   }
# }
# 
# # グローバルテーブルの設定
# resource "aws_dynamodb_table" "price_comparison" {
#   name           = "price-comparison"
#   billing_mode   = "PAY_PER_REQUEST"
#   hash_key       = "id"
#   stream_enabled = true
#   stream_view_type = "NEW_AND_OLD_IMAGES"
# 
#   attribute {
#     name = "id"
#     type = "S"
#   }
# 
#   server_side_encryption {
#     enabled = true
#     kms_key_arn = aws_kms_key.data_encryption.arn
#   }
# 
#   replica {
#     region_name = "ap-southeast-1"
#   }
# 
#   tags = {
#     Name        = "price-comparison"
#     Environment = "production"
#     Project     = "iphone_price_tracker"
#   }
# }

# DynamoDBのバックアップ設定
resource "aws_dynamodb_table" "price_comparison_backup" {
  name             = "price-comparison-backup"
  billing_mode     = "PAY_PER_REQUEST"
  hash_key         = "model"
  stream_enabled   = true
  stream_view_type = "NEW_AND_OLD_IMAGES"

  attribute {
    name = "model"
    type = "S"
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.data_encryption.arn
  }

  tags = {
    Name        = "price-comparison-backup"
    Purpose     = "backup"
    Environment = "production"
    Project     = "iphone_price_tracker"
  }
}

# 新しいバックアップテーブルの設定
resource "aws_dynamodb_table" "price_comparison_backup_v2" {
  name             = "price-comparison-backup-v2"
  billing_mode     = "PAY_PER_REQUEST"
  hash_key         = "model"
  stream_enabled   = true
  stream_view_type = "NEW_AND_OLD_IMAGES"

  attribute {
    name = "model"
    type = "S"
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.data_encryption.arn
  }

  tags = {
    Name        = "price-comparison-backup-v2"
    Purpose     = "backup"
    Environment = "production"
    Project     = "iphone_price_tracker"
  }
}

# Lambda関数のバックアップ設定
resource "aws_lambda_function" "get_prices_backup" {
  filename      = "lambda_function.zip"
  function_name = "${aws_lambda_function.get_prices.function_name}-backup"
  role          = aws_iam_role.lambda_execution_role.arn
  handler       = "get_prices_lambda.lambda_handler"
  runtime       = "python3.9"
  memory_size   = 1024
  timeout       = 15
  publish       = true

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.price_comparison_backup.name
    }
  }

  tags = {
    Name        = "${aws_lambda_function.get_prices.function_name}-backup"
    Environment = var.environment
    Purpose     = "backup"
  }
}

# API Gatewayのバックアップ設定
resource "aws_api_gateway_rest_api" "price_comparison_backup" {
  name        = "${aws_api_gateway_rest_api.price_comparison.name}-backup"
  description = "Backup API for iPhone price comparison"
}

resource "aws_api_gateway_resource" "prices_backup" {
  rest_api_id = aws_api_gateway_rest_api.price_comparison_backup.id
  parent_id   = aws_api_gateway_rest_api.price_comparison_backup.root_resource_id
  path_part   = "get_prices"
}

resource "aws_api_gateway_method" "get_prices_backup" {
  rest_api_id   = aws_api_gateway_rest_api.price_comparison_backup.id
  resource_id   = aws_api_gateway_resource.prices_backup.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "lambda_backup" {
  rest_api_id = aws_api_gateway_rest_api.price_comparison_backup.id
  resource_id = aws_api_gateway_resource.prices_backup.id
  http_method = aws_api_gateway_method.get_prices_backup.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.get_prices_backup.invoke_arn
}

resource "aws_api_gateway_deployment" "api_backup" {
  rest_api_id = aws_api_gateway_rest_api.price_comparison_backup.id

  depends_on = [
    aws_api_gateway_integration.lambda_backup
  ]

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "production_backup" {
  stage_name    = "production"
  rest_api_id   = aws_api_gateway_rest_api.price_comparison_backup.id
  deployment_id = aws_api_gateway_deployment.api_backup.id

  cache_cluster_enabled = true
  cache_cluster_size    = "0.5"

  variables = {
    deployed_at = timestamp()
  }
}

# バックアップの自動化
resource "aws_cloudwatch_event_rule" "backup_schedule" {
  name                = "backup-schedule"
  description         = "定期バックアップのスケジュール"
  schedule_expression = "cron(0 0 * * ? *)" # 毎日午前0時に実行
}

resource "aws_cloudwatch_event_target" "backup_lambda" {
  rule      = aws_cloudwatch_event_rule.backup_schedule.name
  target_id = "BackupLambda"
  arn       = aws_lambda_function.get_prices_backup.arn
}

# バックアップの検証
resource "aws_cloudwatch_metric_alarm" "backup_verification" {
  alarm_name          = "backup-verification"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Invocations"
  namespace           = "AWS/Lambda"
  period              = "86400" # 24時間
  statistic           = "Sum"
  threshold           = "1" # 1回以上の実行
  alarm_description   = "バックアップが24時間以内に実行されていません"
  treat_missing_data  = "breaching"

  dimensions = {
    FunctionName = aws_lambda_function.get_prices_backup.function_name
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
} 