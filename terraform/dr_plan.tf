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
          aws_dynamodb_table.price_comparison.arn,
          aws_dynamodb_table.price_comparison_backup.arn
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
      PRIMARY_TABLE = aws_dynamodb_table.price_comparison.name
      BACKUP_TABLE  = aws_dynamodb_table.price_comparison_backup.name
      PRIMARY_API   = aws_api_gateway_rest_api.price_comparison.id
      BACKUP_API    = aws_api_gateway_rest_api.price_comparison_backup.id
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
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Invocations"
  namespace           = "AWS/Lambda"
  period              = "2592000" # 30日
  statistic           = "Sum"
  threshold           = "1" # 1回以上の実行
  alarm_description   = "ディザスタリカバリテストが30日以内に実行されていません"
  treat_missing_data  = "breaching"

  dimensions = {
    FunctionName = aws_lambda_function.dr_handler.function_name
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
}

# ディザスタリカバリのドキュメント
resource "aws_ssm_document" "dr_plan" {
  name            = "price-comparison-dr-plan"
  document_type   = "Command"
  document_format = "YAML"

  content = <<DOC
schemaVersion: '2.2'
description: Price Comparison App Disaster Recovery Plan
mainSteps:
  - name: "CheckPrimaryRegion"
    action: "aws:invokeLambdaFunction"
    inputs:
      FunctionName: ${aws_lambda_function.dr_handler.function_name}
      Payload: '{"action": "check_primary"}'
  - name: "SwitchToBackup"
    action: "aws:invokeLambdaFunction"
    inputs:
      FunctionName: ${aws_lambda_function.dr_handler.function_name}
      Payload: '{"action": "switch_to_backup"}'
  - name: "VerifyBackup"
    action: "aws:invokeLambdaFunction"
    inputs:
      FunctionName: ${aws_lambda_function.dr_handler.function_name}
      Payload: '{"action": "verify_backup"}'
  - name: "NotifyTeam"
    action: "aws:sns"
    inputs:
      TopicArn: ${aws_sns_topic.alerts.arn}
      Message: "Disaster Recovery Plan executed"
DOC
} 