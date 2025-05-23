locals {
  lambda_src_dir = "${path.module}/.."
  lambda_files = [
    "lambdas/get_prices_lambda/lambda_function.py",
    "lambdas/save_price_history_lambda/save_price_history.py",
    "lambdas/get_price_history_lambda/get_price_history.py",
    "app.py",
    "config/config.production.yaml"
  ]
  layer_build_dir = "${path.module}/layer"
  layer_zip_path  = "${path.module}/layer.zip"
}

# Lambda Layer用のPythonパッケージをインストール
resource "null_resource" "install_lambda_layer_packages" {
  triggers = {
    requirements = filemd5("${path.module}/../requirements-base.txt")
  }

  provisioner "local-exec" {
    command = <<EOF
rm -rf ${local.layer_build_dir}
mkdir -p ${local.layer_build_dir}/python
pip install --no-cache-dir --platform manylinux2014_x86_64 --target=${local.layer_build_dir}/python --implementation cp --python-version 3.9 --only-binary=:all: --upgrade -r ${path.module}/../requirements-base.txt
cd ${local.layer_build_dir} && zip -r ../layer.zip .
EOF
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Lambda Layer
resource "aws_lambda_layer_version" "dependencies" {
  layer_name          = "get_prices_dependencies"
  description         = "Dependencies for get_prices Lambda function"
  compatible_runtimes = ["python3.9"]
  filename            = local.layer_zip_path
  source_code_hash    = null_resource.install_lambda_layer_packages.id

  depends_on = [null_resource.install_lambda_layer_packages]
}

# Lambda関数のソースコードをZIP化
data "archive_file" "lambda_get_prices" {
  type        = "zip"
  output_path = "${path.module}/lambda_function.zip"

  dynamic "source" {
    for_each = local.lambda_files
    content {
      content  = file("${local.lambda_src_dir}/${source.value}")
      filename = basename(source.value)
    }
  }
}

# Get Prices Lambda Function
resource "aws_lambda_function" "get_prices" {
  filename         = "${path.module}/lambda_function.zip"
  function_name    = "get_prices"
  role             = aws_iam_role.lambda_execution_role.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.9"
  source_code_hash = data.archive_file.lambda_get_prices.output_base64sha256
  timeout          = 30
  memory_size      = 128

  environment {
    variables = {
      KAITORI_TABLE  = aws_dynamodb_table.kaitori_prices.name
      OFFICIAL_TABLE = aws_dynamodb_table.official_prices.name
      ENVIRONMENT    = "production"
    }
  }

  tags = {
    Name        = "get_prices"
    Environment = "production"
    Project     = "iphone_price_tracker"
  }
}

# Lambda関数のメモリとタイムアウトの最適化
resource "aws_lambda_function" "price_comparison" {
  filename         = "${path.module}/lambda_function.zip"
  function_name    = "price-comparison-function"
  description      = "Lambda function for price comparison"
  role             = aws_iam_role.lambda_execution_role.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.9"
  timeout          = 30
  memory_size      = 128
  publish          = true
  source_code_hash = data.archive_file.lambda_get_prices.output_base64sha256

  environment {
    variables = {
      KAITORI_TABLE  = aws_dynamodb_table.kaitori_prices.name
      OFFICIAL_TABLE = aws_dynamodb_table.official_prices.name
      ENVIRONMENT    = "production"
    }
  }

  tags = {
    Name        = "price-comparison-function"
    Environment = "production"
    Project     = "iphone_price_tracker"
    Service     = "price-comparison"
  }
}

# Lambda関数のエイリアス
resource "aws_lambda_alias" "get_prices" {
  name             = "production"
  description      = "Production alias for get_prices Lambda function"
  function_name    = aws_lambda_function.price_comparison.function_name
  function_version = aws_lambda_function.price_comparison.version # 公開されたバージョンを使用
}

# Lambda関数のバージョン
resource "aws_lambda_function_event_invoke_config" "get_prices" {
  function_name = aws_lambda_function.price_comparison.function_name

  maximum_event_age_in_seconds = 60
  maximum_retry_attempts       = 2

  destination_config {
    on_failure {
      destination = aws_sqs_queue.lambda_dlq.arn
    }
  }
}

# Lambda関数のデッドレターキュー
resource "aws_sqs_queue" "lambda_dlq" {
  name                       = "get_prices_dlq"
  message_retention_seconds  = 1209600 # 14日間
  visibility_timeout_seconds = 300     # 5分

  tags = {
    Name        = "get_prices_dlq"
    Environment = "production"
    Project     = "iphone_price_tracker"
  }
}

# Lambda関数の自動スケーリング設定
resource "aws_appautoscaling_target" "lambda_target" {
  max_capacity       = 10
  min_capacity       = 2
  resource_id        = "function:${aws_lambda_function.price_comparison.function_name}:${aws_lambda_alias.get_prices.name}"
  scalable_dimension = "lambda:function:ProvisionedConcurrency"
  service_namespace  = "lambda"
}

resource "aws_appautoscaling_policy" "lambda_scaling_policy" {
  name               = "lambda-scaling-policy"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.lambda_target.resource_id
  scalable_dimension = aws_appautoscaling_target.lambda_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.lambda_target.service_namespace

  target_tracking_scaling_policy_configuration {
    target_value       = 0.7 # 70%の使用率を目標に
    scale_in_cooldown  = 300
    scale_out_cooldown = 300

    predefined_metric_specification {
      predefined_metric_type = "LambdaProvisionedConcurrencyUtilization"
    }
  }
}

# デプロイメント検証用のLambda関数
resource "aws_lambda_function" "deployment_verification" {
  filename         = "${path.module}/lambda_function.zip"
  function_name    = "deployment-verification"
  role             = aws_iam_role.deployment_verification.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.9"
  timeout          = 300
  memory_size      = 128
  source_code_hash = data.archive_file.lambda_get_prices.output_base64sha256

  environment {
    variables = {
      LAMBDA_FUNCTION_NAME = aws_lambda_function.price_comparison.function_name
      DYNAMODB_TABLES      = jsonencode([aws_dynamodb_table.kaitori_prices.name, aws_dynamodb_table.official_prices.name])
      API_ID               = aws_api_gateway_rest_api.price_comparison.id
      ENVIRONMENT          = "production"
    }
  }

  tags = {
    Name        = "deployment-verification"
    Environment = "production"
    Project     = "iphone_price_tracker"
  }
}

# スモークテスト用のLambda関数
resource "aws_lambda_function" "smoke_test" {
  filename         = "${path.module}/lambda_function.zip"
  function_name    = "smoke-test"
  role             = aws_iam_role.smoke_test.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.9"
  timeout          = 300
  memory_size      = 128
  source_code_hash = data.archive_file.lambda_get_prices.output_base64sha256

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.kaitori_prices.name
      ENVIRONMENT    = "production"
    }
  }

  tags = {
    Name        = "smoke-test"
    Environment = "production"
    Project     = "iphone_price_tracker"
  }
}

# 価格履歴保存用のLambda関数
resource "aws_lambda_function" "save_price_history" {
  filename      = "save_price_history.zip"
  function_name = "save-price-history"
  role          = aws_iam_role.lambda_execution_role.arn
  handler       = "save_price_history.lambda_handler"
  runtime       = "python3.9"
  timeout       = 300
  memory_size   = 128

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.price_history.name
      ENVIRONMENT    = "production"
    }
  }

  tags = {
    Name        = "save-price-history"
    Environment = "production"
    Project     = "iphone_price_tracker"
  }
}

# 価格履歴保存のスケジュール設定
resource "aws_cloudwatch_event_rule" "save_price_history_schedule" {
  name                = "save-price-history-schedule"
  description         = "毎日価格履歴を保存"
  schedule_expression = "cron(0 0 * * ? *)" # 毎日午前0時
}

resource "aws_cloudwatch_event_target" "save_price_history_target" {
  rule      = aws_cloudwatch_event_rule.save_price_history_schedule.name
  target_id = "SavePriceHistory"
  arn       = aws_lambda_function.save_price_history.arn
}

resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.save_price_history.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.save_price_history_schedule.arn
}

# 価格履歴取得用のLambda関数
resource "aws_lambda_function" "get_price_history" {
  filename      = "get_price_history.zip"
  function_name = "get-price-history"
  role          = aws_iam_role.lambda_execution_role.arn
  handler       = "get_price_history.lambda_handler"
  runtime       = "python3.9"
  timeout       = 300
  memory_size   = 128

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.price_history.name
      ENVIRONMENT    = "production"
    }
  }

  tags = {
    Name        = "get-price-history"
    Environment = "production"
    Project     = "iphone_price_tracker"
  }
}

# 価格チェック用のLambda関数
resource "aws_lambda_function" "check_prices_lambda" {
  filename      = "check_prices.zip"
  function_name = "check-prices"
  role          = aws_iam_role.lambda_execution_role.arn
  handler       = "check_prices.lambda_handler"
  runtime       = "python3.9"
  timeout       = 300
  memory_size   = 128

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.kaitori_prices.name
      ENVIRONMENT    = "production"
    }
  }

  tags = {
    Name        = "check-prices"
    Environment = "production"
    Project     = "iphone_price_tracker"
  }
}

# 価格チェックのスケジュール設定
resource "aws_cloudwatch_event_rule" "check_prices_schedule" {
  name                = "check-prices-schedule"
  description         = "毎日価格をチェック"
  schedule_expression = "cron(0 0 * * ? *)" # 毎日午前0時
}

resource "aws_cloudwatch_event_target" "check_prices_target" {
  rule      = aws_cloudwatch_event_rule.check_prices_schedule.name
  target_id = "CheckPrices"
  arn       = aws_lambda_function.check_prices_lambda.arn
}

resource "aws_lambda_permission" "check_prices_lambda_permission" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.check_prices_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.check_prices_schedule.arn
}

# LINE通知用のLambda関数
resource "aws_lambda_function" "line_notification_lambda" {
  filename      = "line_notification.zip"
  function_name = "line-notification"
  role          = aws_iam_role.lambda_execution_role.arn
  handler       = "line_notification.lambda_handler"
  runtime       = "python3.9"
  timeout       = 300
  memory_size   = 128

  environment {
    variables = {
      LINE_CHANNEL_ACCESS_TOKEN = var.line_channel_access_token
      LINE_NOTIFY_TOKEN         = var.line_notify_token
      ENVIRONMENT               = "production"
    }
  }

  tags = {
    Name        = "line-notification"
    Environment = "production"
    Project     = "iphone_price_tracker"
  }
}

# 価格比較用のLambda関数
resource "aws_lambda_function" "compare_prices_lambda" {
  filename      = "compare_prices.zip"
  function_name = "compare-prices"
  role          = aws_iam_role.lambda_execution_role.arn
  handler       = "compare_prices.lambda_handler"
  runtime       = "python3.9"
  timeout       = 300
  memory_size   = 128

  environment {
    variables = {
      KAITORI_TABLE  = aws_dynamodb_table.kaitori_prices.name
      OFFICIAL_TABLE = aws_dynamodb_table.official_prices.name
      ENVIRONMENT    = "production"
    }
  }

  tags = {
    Name        = "compare-prices"
    Environment = "production"
    Project     = "iphone_price_tracker"
  }
}

