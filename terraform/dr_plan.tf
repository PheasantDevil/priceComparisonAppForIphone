# ディザスタリカバリ用のIAMロール
resource "aws_iam_role" "dr_role" {
  name = "price-comparison-dr-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "dr_policy" {
  name = "price-comparison-dr-policy"
  role = aws_iam_role.dr_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:DescribeTable",
          "dynamodb:Scan",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:BatchWriteItem",
          "dynamodb:BatchGetItem",
          "dynamodb:DescribeTable"
        ]
        Resource = [
          aws_dynamodb_table.kaitori_prices.arn,
          aws_dynamodb_table.official_prices.arn,
          aws_dynamodb_table.price_history.arn,
          aws_dynamodb_table.price_predictions.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# ディザスタリカバリ用のLambda関数
resource "aws_lambda_function" "dr_handler" {
  filename      = "lambda_function.zip"
  function_name = "price-comparison-dr-handler"
  role          = aws_iam_role.dr_role.arn
  handler       = "dr_handler.lambda_handler"
  runtime       = "python3.9"
  memory_size   = 1024
  timeout       = 300 # 5分

  environment {
    variables = {
      KAITORI_TABLE = aws_dynamodb_table.kaitori_prices.name
      OFFICIAL_TABLE = aws_dynamodb_table.official_prices.name
      HISTORY_TABLE = aws_dynamodb_table.price_history.name
      PREDICTIONS_TABLE = aws_dynamodb_table.price_predictions.name
    }
  }

  tags = {
    Name        = "price-comparison-dr-handler"
    Environment = var.environment
    Purpose     = "disaster-recovery"
  }
}

# ディザスタリカバリの自動化
resource "aws_cloudwatch_event_rule" "dr_test" {
  name                = "dr-test-schedule"
  description         = "ディザスタリカバリテストのスケジュール"
  schedule_expression = "cron(0 0 1 * ? *)" # 毎月1日午前0時に実行
}

resource "aws_cloudwatch_event_target" "dr_test" {
  rule      = aws_cloudwatch_event_rule.dr_test.name
  target_id = "DRTest"
  arn       = aws_lambda_function.dr_handler.arn
}

# ディザスタリカバリの検証
resource "aws_cloudwatch_metric_alarm" "dr_verification" {
  alarm_name          = "dr-verification"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period             = 300  # 5分に変更
  statistic          = "Sum"
  threshold          = 0
  alarm_description  = "DR verification Lambda function errors"
  alarm_actions      = [aws_sns_topic.alerts.arn]

  dimensions = {
    FunctionName = aws_lambda_function.dr_handler.function_name
  }

  tags = {
    Name        = "dr-verification"
    Environment = "production"
    Project     = "iphone_price_tracker"
  }
}

# ディザスタリカバリのドキュメント
resource "aws_ssm_document" "dr_plan" {
  name            = "dr-plan"
  document_type   = "Command"
  document_format = "YAML"

  content = <<DOC
schemaVersion: '2.2'
description: Disaster Recovery Plan
mainSteps:
  - action: aws:runPowerShellScript
    name: invokeDRHandler
    inputs:
      runCommand:
        - aws lambda invoke --function-name price-comparison-dr-handler response.json
DOC
} 