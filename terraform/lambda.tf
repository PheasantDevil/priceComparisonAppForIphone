data "archive_file" "lambda_get_prices" {
  type        = "zip"
  source_dir  = "${path.module}/lambda/get_prices"
  output_path = "${path.module}/lambda/get_prices.zip"
  excludes    = ["__pycache__", "*.pyc"]
}

resource "aws_lambda_function" "get_prices" {
  filename         = data.archive_file.lambda_get_prices.output_path
  function_name    = "get_prices"
  role             = try(
    data.aws_iam_role.existing_lambda_role[0].arn,
    try(aws_iam_role.lambda_role[0].arn, "")
  )
  handler          = "lambda_function.lambda_handler"
  source_code_hash = data.archive_file.lambda_get_prices.output_base64sha256
  runtime          = "python3.9"
  timeout          = 30
  memory_size      = 512 # メモリサイズを増やす

  environment {
    variables = {
      ENVIRONMENT = "production"
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic,
    aws_iam_role_policy.dynamodb_access
  ]
}
