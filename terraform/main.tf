terraform {
  required_version = ">= 1.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.99.1"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "2.7.1"
    }
  }
}

provider "archive" {}

# 現在のAWSアカウントIDを取得
data "aws_caller_identity" "current" {}

# 現在のリージョンを取得
data "aws_region" "current" {}

# CloudWatch Eventsルール
resource "aws_cloudwatch_event_rule" "check_prices" {
  name                = "check-prices"
  description         = "定期的に価格をチェックする"
  schedule_expression = "rate(1 hour)"
}

resource "aws_cloudwatch_event_target" "check_prices" {
  rule      = aws_cloudwatch_event_rule.check_prices.name
  target_id = "CheckPrices"
  arn       = aws_lambda_function.check_prices_lambda.arn
}

resource "aws_lambda_permission" "cloudwatch" {
  statement_id  = "AllowCloudWatchInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.check_prices_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.check_prices.arn
} 