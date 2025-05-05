# メンテナンスウィンドウの設定
resource "aws_ssm_maintenance_window" "price_comparison" {
  name              = "price-comparison-maintenance"
  description       = "Maintenance window for price comparison system"
  schedule          = "cron(0 2 ? * SUN *)" # 毎週日曜日の午前2時
  duration          = 2                     # 2時間
  cutoff            = 1                     # 1時間前までにタスクを開始
  schedule_timezone = "Asia/Tokyo"          # 日本時間
}

# メンテナンスウィンドウのターゲット
resource "aws_ssm_maintenance_window_target" "lambda" {
  window_id     = aws_ssm_maintenance_window.price_comparison.id
  name          = "lambda-maintenance-target"
  description   = "Target for Lambda function maintenance"
  resource_type = "INSTANCE"

  targets {
    key    = "tag:Environment"
    values = [var.environment]
  }
}

# メンテナンスタスク
resource "aws_ssm_maintenance_window_task" "lambda_cleanup" {
  window_id        = aws_ssm_maintenance_window.price_comparison.id
  task_type        = "RUN_COMMAND"
  task_arn         = "AWS-RunShellScript"
  priority         = 1
  service_role_arn = aws_iam_role.maintenance_window.arn
  max_concurrency  = "1"
  max_errors       = "1"

  targets {
    key    = "WindowTargetIds"
    values = [aws_ssm_maintenance_window_target.lambda.id]
  }

  task_invocation_parameters {
    run_command_parameters {
      timeout_seconds = 600

      parameter {
        name = "commands"
        values = [
          "aws lambda update-function-configuration --function-name ${aws_lambda_function.get_prices.function_name} --environment '{\"Variables\":{\"MAINTENANCE_MODE\":\"true\"}}'",
          "sleep 300",
          "aws lambda update-function-configuration --function-name ${aws_lambda_function.get_prices.function_name} --environment '{\"Variables\":{\"MAINTENANCE_MODE\":\"false\"}}'"
        ]
      }
    }
  }
}

# メンテナンスウィンドウ用のIAMロール
resource "aws_iam_role" "maintenance_window" {
  name = "maintenance-window-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ssm.amazonaws.com"
        }
      }
    ]
  })
}

# メンテナンスウィンドウ用のIAMポリシー
resource "aws_iam_role_policy" "maintenance_window" {
  name = "maintenance-window-policy"
  role = aws_iam_role.maintenance_window.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:UpdateFunctionConfiguration",
          "lambda:GetFunctionConfiguration"
        ]
        Resource = aws_lambda_function.get_prices.arn
      }
    ]
  })
} 