# コストアラートの設定
resource "aws_budgets_budget" "monthly" {
  name              = "price-comparison-monthly-budget"
  budget_type       = "COST"
  limit_amount      = "1000" # 月間予算1000ドル
  limit_unit        = "USD"
  time_unit         = "MONTHLY"
  time_period_start = "2024-01-01_00:00"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80 # 予算の80%を超えたら通知
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.alert_email]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100 # 予算を超えたら通知
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = [var.alert_email]
  }
}

# リソース使用量の監視
resource "aws_cloudwatch_metric_alarm" "lambda_cost" {
  alarm_name          = "lambda-cost-alarm"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "EstimatedCharges"
  namespace           = "AWS/Billing"
  period              = "21600" # 6時間
  statistic           = "Maximum"
  threshold           = "50" # 50ドル
  alarm_description   = "Lambda関数の推定コストが閾値を超えました"
  treat_missing_data  = "notBreaching"

  dimensions = {
    ServiceName = "AWSLambda"
    Currency    = "USD"
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
}

resource "aws_cloudwatch_metric_alarm" "dynamodb_cost" {
  alarm_name          = "dynamodb-cost-alarm"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "EstimatedCharges"
  namespace           = "AWS/Billing"
  period              = "21600" # 6時間
  statistic           = "Maximum"
  threshold           = "30" # 30ドル
  alarm_description   = "DynamoDBの推定コストが閾値を超えました"
  treat_missing_data  = "notBreaching"

  dimensions = {
    ServiceName = "AmazonDynamoDB"
    Currency    = "USD"
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
}

# コスト最適化のためのメトリクス
resource "aws_cloudwatch_metric_alarm" "lambda_invocations" {
  alarm_name          = "lambda-invocations-alarm"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Invocations"
  namespace           = "AWS/Lambda"
  period              = "3600" # 1時間
  statistic           = "Sum"
  threshold           = "1000" # 1時間あたり1000回
  alarm_description   = "Lambda関数の呼び出し回数が多すぎます"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.get_prices.function_name
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
}

resource "aws_cloudwatch_metric_alarm" "dynamodb_capacity_units" {
  alarm_name          = "dynamodb-capacity-units-alarm"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "ConsumedReadCapacityUnits"
  namespace           = "AWS/DynamoDB"
  period              = "3600" # 1時間
  statistic           = "Sum"
  threshold           = "10000" # 1時間あたり10000ユニット
  alarm_description   = "DynamoDBの読み取り容量ユニットが多すぎます"
  treat_missing_data  = "notBreaching"

  dimensions = {
    TableName = aws_dynamodb_table.price_comparison.name
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
}

# リソースタグの設定
resource "aws_resourcegroups_group" "cost_optimization" {
  name        = "cost-optimization-group"
  description = "Resources for cost optimization"

  resource_query {
    query = jsonencode({
      ResourceTypeFilters = ["AWS::AllSupported"]
      TagFilters = [
        {
          Key    = "Environment"
          Values = [var.environment]
        },
        {
          Key    = "CostCenter"
          Values = ["PriceComparison"]
        }
      ]
    })
  }
}

# コスト最適化のためのCloudWatchアラーム
resource "aws_cloudwatch_metric_alarm" "cost_anomaly" {
  alarm_name          = "cost-anomaly-alarm"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "AnomalyScore"
  namespace           = "AWS/CostExplorer"
  period              = "86400"
  statistic           = "Maximum"
  threshold           = "80"
  alarm_description   = "コストの異常を検知しました"
  treat_missing_data  = "notBreaching"

  alarm_actions = [aws_sns_topic.alerts.arn]
} 