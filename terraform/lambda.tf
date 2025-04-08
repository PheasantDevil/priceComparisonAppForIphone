locals {
  lambda_src_dir = "${path.module}/.."
  lambda_files = [
    "lambda/get_prices_lambda/lambda_function.py",
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
  filename           = "./layer/layer.zip"
  source_code_hash   = null_resource.install_lambda_layer_packages.id

  depends_on = [null_resource.install_lambda_layer_packages]
}

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

# Lambda関数
resource "aws_lambda_function" "get_prices" {
  filename         = data.archive_file.lambda_get_prices.output_path
  function_name    = "get_prices"
  role             = aws_iam_role.lambda_role.arn
  handler          = "lambda/get_prices_lambda/lambda_function.lambda_handler"
  source_code_hash = data.archive_file.lambda_get_prices.output_base64sha256
  runtime          = "python3.9"
  timeout          = 60
  memory_size      = 256
  layers           = [aws_lambda_layer_version.dependencies.arn]

  environment {
    variables = {
      PYTHONPATH = "/opt/python:/var/task"
    }
  }

  depends_on = [
    aws_iam_role.lambda_role,
    aws_iam_role_policy_attachment.lambda_basic,
    aws_iam_role_policy.dynamodb_access
  ]
}

resource "aws_lambda_function" "save_price_history" {
  filename         = "lambda_function.zip"
  function_name    = "save_price_history"
  role             = aws_iam_role.lambda_role.arn
  handler          = "save_price_history.lambda_handler"
  runtime          = "python3.9"
  timeout          = 300
  memory_size      = 128

  environment {
    variables = {
      DYNAMODB_TABLE = "price_history"
    }
  }
}

resource "aws_cloudwatch_event_rule" "save_price_history_schedule" {
  name                = "save_price_history_schedule"
  description         = "Schedule for saving price history"
  schedule_expression = "cron(0 1,13 * * ? *)"  # 10:00 and 22:00 JST
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
