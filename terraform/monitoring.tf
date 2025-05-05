# CloudWatchのモニタリング設定

# Lambda関数のエラーアラーム
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "get_prices_lambda_errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300" # 5分
  statistic           = "Sum"
  threshold           = "0"
  alarm_description   = "Lambda関数のエラー発生を検知"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.get_prices.function_name
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
}

# Lambda関数の実行時間アラーム
resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  alarm_name          = "lambda-duration-alarm"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "3"
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Average"
  threshold           = "1000" # 1秒
  alarm_description   = "Lambda関数の実行時間が長すぎます"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.get_prices.function_name
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
}

# API Gatewayのエラーアラーム
resource "aws_cloudwatch_metric_alarm" "api_gateway_errors" {
  alarm_name          = "price_comparison_api_errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "5XXError"
  namespace           = "AWS/ApiGateway"
  period              = "300" # 5分
  statistic           = "Sum"
  threshold           = "0"
  alarm_description   = "API Gatewayの5XXエラー発生を検知"
  treat_missing_data  = "notBreaching"

  dimensions = {
    ApiName = aws_api_gateway_rest_api.price_comparison.name
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
}

# DynamoDBの容量アラーム
resource "aws_cloudwatch_metric_alarm" "dynamodb_capacity" {
  alarm_name          = "price_comparison_dynamodb_capacity"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "ConsumedReadCapacityUnits"
  namespace           = "AWS/DynamoDB"
  period              = "300" # 5分
  statistic           = "Sum"
  threshold           = "1000" # 1,000ユニット
  alarm_description   = "DynamoDBの読み取り容量が高い"
  treat_missing_data  = "notBreaching"

  dimensions = {
    TableName = aws_dynamodb_table.price_comparison.name
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
}

# SNSトピックの作成
resource "aws_sns_topic" "alerts" {
  name = "price_comparison_alerts"
}

# SNSトピックのポリシー
resource "aws_sns_topic_policy" "alerts" {
  arn    = aws_sns_topic.alerts.arn
  policy = data.aws_iam_policy_document.sns_topic_policy.json
}

# SNSトピックのポリシードキュメント
data "aws_iam_policy_document" "sns_topic_policy" {
  statement {
    effect    = "Allow"
    actions   = ["SNS:Publish"]
    resources = [aws_sns_topic.alerts.arn]

    principals {
      type        = "Service"
      identifiers = ["cloudwatch.amazonaws.com"]
    }
  }
}

# CloudWatchダッシュボード
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "price-comparison-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/Lambda", "Errors", "FunctionName", aws_lambda_function.get_prices.function_name],
            ["AWS/Lambda", "Duration", "FunctionName", aws_lambda_function.get_prices.function_name]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "Lambda Function Metrics"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/ApiGateway", "5XXError", "ApiName", aws_api_gateway_rest_api.price_comparison.name],
            ["AWS/ApiGateway", "4XXError", "ApiName", aws_api_gateway_rest_api.price_comparison.name]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "API Gateway Errors"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/DynamoDB", "ConsumedReadCapacityUnits", "TableName", aws_dynamodb_table.price_comparison.name],
            ["AWS/DynamoDB", "ConsumedWriteCapacityUnits", "TableName", aws_dynamodb_table.price_comparison.name]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "DynamoDB Capacity"
        }
      },
      {
        type   = "log"
        x      = 0
        y      = 12
        width  = 12
        height = 6

        properties = {
          query  = "SOURCE '/aws/lambda/${aws_lambda_function.get_prices.function_name}' | fields @timestamp, @message | filter @message like /ERROR/ | sort @timestamp desc | limit 20"
          region = var.aws_region
          title  = "Lambda Error Logs"
          view   = "table"
        }
      },
      {
        type   = "log"
        x      = 12
        y      = 12
        width  = 12
        height = 6

        properties = {
          query  = "SOURCE '/aws/apigateway/${aws_api_gateway_rest_api.price_comparison.name}' | fields @timestamp, @message | filter @message like /error/ | sort @timestamp desc | limit 20"
          region = var.aws_region
          title  = "API Gateway Error Logs"
          view   = "table"
        }
      }
    ]
  })
}

# CloudWatch Logs Insightsのクエリ定義
resource "aws_cloudwatch_query_definition" "lambda_errors" {
  name = "lambda-errors"
  log_group_names = [
    "/aws/lambda/${aws_lambda_function.get_prices.function_name}"
  ]
  query_string = <<EOF
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
| limit 20
EOF
}

resource "aws_cloudwatch_query_definition" "api_errors" {
  name = "api-errors"
  log_group_names = [
    "/aws/apigateway/${aws_api_gateway_rest_api.price_comparison.name}"
  ]
  query_string = <<EOF
fields @timestamp, @message
| filter @message like /error/
| sort @timestamp desc
| limit 20
EOF
}

# ロググループの保持期間設定
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${aws_lambda_function.get_prices.function_name}"
  retention_in_days = 30
}

resource "aws_cloudwatch_log_group" "api_gateway_logs" {
  name              = "/aws/apigateway/price-comparison-api"
  retention_in_days = 30

  lifecycle {
    prevent_destroy = true
  }

  tags = {
    Name        = "api-gateway-logs"
    Environment = "production"
    Project     = "iphone_price_tracker"
  }
}

# カスタムメトリクスの定義
resource "aws_cloudwatch_metric_alarm" "custom_error_rate" {
  alarm_name          = "price_comparison_error_rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "ErrorRate"
  namespace           = "Custom/PriceComparison"
  period              = "300"
  statistic           = "Average"
  threshold           = "0.1" # 10%のエラーレート
  alarm_description   = "カスタムエラーレートが閾値を超えました"
  treat_missing_data  = "notBreaching"

  dimensions = {
    Service = "PriceComparison"
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
}

# パフォーマンスモニタリングのためのCloudWatchダッシュボード
resource "aws_cloudwatch_dashboard" "performance" {
  dashboard_name = "performance-dashboard"
  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/Lambda", "Duration", "FunctionName", aws_lambda_function.get_prices.function_name],
            ["AWS/Lambda", "ConcurrentExecutions", "FunctionName", aws_lambda_function.get_prices.function_name]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "Lambda Performance"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/DynamoDB", "ConsumedReadCapacityUnits", "TableName", aws_dynamodb_table.iphone_prices.name],
            ["AWS/DynamoDB", "ConsumedWriteCapacityUnits", "TableName", aws_dynamodb_table.iphone_prices.name]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "DynamoDB Throughput"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/ApiGateway", "Latency", "ApiName", aws_api_gateway_rest_api.price_comparison.name],
            ["AWS/ApiGateway", "IntegrationLatency", "ApiName", aws_api_gateway_rest_api.price_comparison.name]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "API Gateway Latency"
        }
      }
    ]
  })
}

# パフォーマンスアラームの設定
resource "aws_cloudwatch_metric_alarm" "api_latency" {
  alarm_name          = "api-latency-alarm"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "3"
  metric_name         = "Latency"
  namespace           = "AWS/ApiGateway"
  period              = "300"
  statistic           = "Average"
  threshold           = "500" # 500ミリ秒
  alarm_description   = "API Gatewayのレイテンシーが高すぎます"
  treat_missing_data  = "notBreaching"

  dimensions = {
    ApiName = aws_api_gateway_rest_api.price_comparison.name
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
}

# パフォーマンスログの設定
resource "aws_cloudwatch_log_group" "performance" {
  name              = "/aws/lambda/performance-logs"
  retention_in_days = 30

  tags = {
    Environment = var.environment
    Purpose     = "PerformanceMonitoring"
  }
}

# パフォーマンスメトリクスのフィルター
resource "aws_cloudwatch_log_metric_filter" "slow_requests" {
  name           = "slow-requests-filter"
  pattern        = "{ $.duration > 1000 }"
  log_group_name = aws_cloudwatch_log_group.performance.name

  metric_transformation {
    name      = "SlowRequests"
    value     = "1"
    namespace = "Custom/Performance"
  }
} 