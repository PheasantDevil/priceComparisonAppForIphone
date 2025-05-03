locals {
  lambda_src_dir = "${path.module}/.."
  lambda_files = [
    "lambda/get_prices_lambda/lambda_function.py",
    "lambda/save_price_history_lambda/save_price_history.py",
    "lambda/get_price_history_lambda/get_price_history.py",
    "src/apple_scraper_for_rudea.py",
    "config/config.production.yaml"
  ]
  layer_build_dir = "${path.module}/layer"
  layer_zip_path  = "${path.module}/layer.zip"
}

# Lambda Layer用のPythonパッケージをインストール
resource "null_resource" "install_lambda_layer_packages" {
  triggers = {
    requirements = filemd5("${path.module}/requirements.txt")
  }

  provisioner "local-exec" {
    command = <<EOF
rm -rf ${local.layer_build_dir}
mkdir -p ${local.layer_build_dir}/python
pip install -r ${path.module}/requirements.txt -t ${local.layer_build_dir}/python
cd ${local.layer_build_dir} && zip -r ${local.layer_zip_path} .
EOF
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
      filename = source.value
    }
  }
}

# Get Prices Lambda Function
resource "aws_lambda_function" "get_prices" {
  filename         = data.archive_file.lambda_get_prices.output_path
  function_name    = "get_prices"
  role             = aws_iam_role.lambda_role.arn
  handler          = "get_prices.lambda_handler"
  runtime          = "python3.9"
  timeout          = 30
  memory_size      = 128
  source_code_hash = data.archive_file.lambda_get_prices.output_base64sha256

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.iphone_prices.name
    }
  }
}

# Lambda関数のメモリとタイムアウトの最適化
resource "aws_lambda_function" "price_comparison" {
  filename      = "lambda_function.zip"
  function_name = "price-comparison-function"
  description   = "Lambda function for price comparison"
  role          = aws_iam_role.lambda_execution_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.9"
  timeout       = 30
  memory_size   = 128

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.iphone_prices.name
    }
  }

  tags = {
    Environment = "production"
    Service     = "price-comparison"
  }
}

# Lambda関数のエイリアス
resource "aws_lambda_alias" "get_prices" {
  name             = "production"
  description      = "Production alias for get_prices Lambda function"
  function_name    = aws_lambda_function.price_comparison.function_name
  function_version = "$LATEST"
}

# Lambda関数のバージョン
resource "aws_lambda_function_event_invoke_config" "get_prices" {
  function_name = aws_lambda_function.price_comparison.function_name

  # 同時実行数の制限
  maximum_event_age_in_seconds = 60
  maximum_retry_attempts       = 2

  # デッドレターキュー
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
    Environment = var.environment
    Project     = "price_comparison"
  }
}

# Lambda関数のコールドスタート対策
resource "aws_lambda_provisioned_concurrency_config" "get_prices" {
  function_name                     = aws_lambda_function.price_comparison.function_name
  provisioned_concurrent_executions = 5
  qualifier                         = aws_lambda_alias.get_prices.name
}

# Lambda関数の自動スケーリング設定
resource "aws_appautoscaling_target" "lambda_target" {
  max_capacity       = 100
  min_capacity       = 5
  resource_id        = "function:${aws_lambda_function.price_comparison.function_name}:${aws_lambda_alias.get_prices.name}"
  scalable_dimension = "lambda:function:ProvisionedConcurrency"
  service_namespace  = "lambda"
}

resource "aws_appautoscaling_policy" "lambda_scaling_policy" {
  name               = "lambda-concurrency-scaling-policy"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.lambda_target.resource_id
  scalable_dimension = aws_appautoscaling_target.lambda_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.lambda_target.service_namespace

  target_tracking_scaling_policy_configuration {
    target_value       = 70.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 300

    predefined_metric_specification {
      predefined_metric_type = "LambdaProvisionedConcurrencyUtilization"
    }
  }
}

# デプロイメント検証用のLambda関数
resource "aws_lambda_function" "deployment_verification" {
  filename      = "deployment_verification.zip"
  function_name = "deployment-verification"
  role          = aws_iam_role.deployment_verification.arn
  handler       = "verify_deployment.lambda_handler"
  runtime       = "python3.9"
  timeout       = 300
  memory_size   = 128

  environment {
    variables = {
      LAMBDA_FUNCTION_NAME = aws_lambda_function.price_comparison.function_name
      DYNAMODB_TABLES      = jsonencode([aws_dynamodb_table.iphone_prices.name, aws_dynamodb_table.official_prices.name])
      API_ID               = aws_api_gateway_rest_api.price_comparison.id
    }
  }
}

# スモークテスト用のLambda関数
resource "aws_lambda_function" "smoke_test" {
  filename      = "smoke_test.zip"
  function_name = "smoke-test"
  role          = aws_iam_role.smoke_test.arn
  handler       = "run_smoke_tests.lambda_handler"
  runtime       = "python3.9"
  timeout       = 300
  memory_size   = 128

  environment {
    variables = {
      LAMBDA_FUNCTION_NAME = aws_lambda_function.price_comparison.function_name
      DYNAMODB_TABLES      = jsonencode([aws_dynamodb_table.iphone_prices.name, aws_dynamodb_table.official_prices.name])
      API_URL              = "https://${aws_api_gateway_rest_api.price_comparison.id}.execute-api.${var.aws_region}.amazonaws.com/production/prices"
    }
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
      DYNAMODB_TABLE = aws_dynamodb_table.iphone_prices.name
    }
  }
}

# 価格履歴保存用のCloudWatchイベントルール
resource "aws_cloudwatch_event_rule" "save_price_history_schedule" {
  name                = "save-price-history-schedule"
  description         = "Schedule for saving price history"
  schedule_expression = "rate(1 hour)"
}

# 価格履歴保存用のCloudWatchイベントターゲット
resource "aws_cloudwatch_event_target" "save_price_history_target" {
  rule      = aws_cloudwatch_event_rule.save_price_history_schedule.name
  target_id = "SavePriceHistory"
  arn       = aws_lambda_function.save_price_history.arn
}

# 価格履歴保存用のLambdaパーミッション
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
      DYNAMODB_TABLE = aws_dynamodb_table.iphone_prices.name
    }
  }
}

resource "aws_lambda_function" "predict_prices_lambda" {
  filename         = "lambdas/predict_prices_lambda/predict_prices.zip"
  function_name    = "predict_prices_lambda"
  role             = aws_iam_role.lambda_role.arn
  handler          = "predict_prices.lambda_handler"
  runtime          = "python3.9"
  timeout          = 30
  memory_size      = 256

  environment {
    variables = {
      ENVIRONMENT = var.environment
    }
  }

  tags = {
    Name        = "predict_prices_lambda"
    Environment = var.environment
  }
}

resource "aws_lambda_permission" "predict_prices_lambda_permission" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.predict_prices_lambda.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

resource "aws_lambda_function" "compare_prices_lambda" {
  filename         = "lambdas/compare_prices_lambda/compare_prices.zip"
  function_name    = "compare_prices_lambda"
  role             = aws_iam_role.lambda_role.arn
  handler          = "compare_prices.lambda_handler"
  runtime          = "python3.9"
  timeout          = 30
  memory_size      = 256

  environment {
    variables = {
      ENVIRONMENT = var.environment
    }
  }

  tags = {
    Name        = "compare_prices_lambda"
    Environment = var.environment
  }
}

resource "aws_lambda_permission" "compare_prices_lambda_permission" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.compare_prices_lambda.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}
