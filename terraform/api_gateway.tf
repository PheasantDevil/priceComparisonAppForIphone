# API Gatewayの認証用のIAMロール
resource "aws_iam_role" "api_gateway_auth" {
  name = "api_gateway_auth_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "apigateway.amazonaws.com"
        }
      }
    ]
  })
}

# API Gatewayの認証用ポリシー
resource "aws_iam_role_policy" "api_gateway_auth" {
  name = "api_gateway_auth_policy"
  role = aws_iam_role.api_gateway_auth.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      }
    ]
  })
}

# API Gatewayの設定
resource "aws_api_gateway_rest_api" "price_comparison" {
  name        = "price-comparison-api"
  description = "API for iPhone price comparison"
}

# API Gatewayのリソース
resource "aws_api_gateway_resource" "prices" {
  rest_api_id = aws_api_gateway_rest_api.price_comparison.id
  parent_id   = aws_api_gateway_rest_api.price_comparison.root_resource_id
  path_part   = "get_prices"
}

# API Gatewayのメソッド（認証付き）
resource "aws_api_gateway_method" "get_prices" {
  rest_api_id   = aws_api_gateway_rest_api.price_comparison.id
  resource_id   = aws_api_gateway_resource.prices.id
  http_method   = "GET"
  authorization = "NONE"
}

# API Gatewayの統合
resource "aws_api_gateway_integration" "lambda" {
  rest_api_id = aws_api_gateway_rest_api.price_comparison.id
  resource_id = aws_api_gateway_resource.prices.id
  http_method = aws_api_gateway_method.get_prices.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.get_prices.invoke_arn
}

# API Gatewayのデプロイメント
resource "aws_api_gateway_deployment" "api" {
  rest_api_id = aws_api_gateway_rest_api.price_comparison.id

  depends_on = [
    aws_api_gateway_integration.lambda
  ]

  lifecycle {
    create_before_destroy = true
  }
}

# API Gatewayのステージ設定
resource "aws_api_gateway_stage" "production" {
  stage_name    = "production"
  rest_api_id   = aws_api_gateway_rest_api.price_comparison.id
  deployment_id = aws_api_gateway_deployment.api.id

  cache_cluster_enabled = true
  cache_cluster_size    = "0.5" # 0.5GBのキャッシュ

  variables = {
    deployed_at = timestamp()
  }
}

# API Gatewayのキャッシュポリシー
resource "aws_api_gateway_method_settings" "get_prices" {
  rest_api_id = aws_api_gateway_rest_api.price_comparison.id
  stage_name  = aws_api_gateway_stage.production.stage_name
  method_path = "${aws_api_gateway_resource.prices.path_part}/${aws_api_gateway_method.get_prices.http_method}"

  settings {
    metrics_enabled      = true
    logging_level        = "INFO"
    caching_enabled      = true
    cache_ttl_in_seconds = 300 # 5分間のキャッシュ
  }
}

# CloudWatch Logsグループ
resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "/aws/apigateway/price-comparison"
  retention_in_days = 30
}

# Lambdaの権限設定
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_prices.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.price_comparison.execution_arn}/*/*"
}

# API Gatewayのメソッドレスポンス
resource "aws_api_gateway_method_response" "get_prices" {
  rest_api_id = aws_api_gateway_rest_api.price_comparison.id
  resource_id = aws_api_gateway_resource.prices.id
  http_method = aws_api_gateway_method.get_prices.http_method
  status_code = "200"

  response_models = {
    "application/json" = "Empty"
  }

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

# API Gatewayの統合レスポンス
resource "aws_api_gateway_integration_response" "get_prices" {
  rest_api_id = aws_api_gateway_rest_api.price_comparison.id
  resource_id = aws_api_gateway_resource.prices.id
  http_method = aws_api_gateway_method.get_prices.http_method
  status_code = aws_api_gateway_method_response.get_prices.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = "'*'"
  }

  depends_on = [
    aws_api_gateway_integration.lambda
  ]
}
