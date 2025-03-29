resource "aws_api_gateway_rest_api" "price_comparison" {
  name        = "price-comparison-api"
  description = "API for iPhone price comparison"
}

resource "aws_api_gateway_resource" "prices" {
  rest_api_id = aws_api_gateway_rest_api.price_comparison.id
  parent_id   = aws_api_gateway_rest_api.price_comparison.root_resource_id
  path_part   = "get_prices"
}

resource "aws_api_gateway_method" "get_prices" {
  rest_api_id   = aws_api_gateway_rest_api.price_comparison.id
  resource_id   = aws_api_gateway_resource.prices.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "lambda" {
  rest_api_id = aws_api_gateway_rest_api.price_comparison.id
  resource_id = aws_api_gateway_resource.prices.id
  http_method = aws_api_gateway_method.get_prices.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = try(
    data.aws_lambda_function.existing_get_prices.invoke_arn,
    try(aws_lambda_function.get_prices[0].invoke_arn, "")
  )
}

resource "aws_api_gateway_deployment" "api" {
  rest_api_id = aws_api_gateway_rest_api.price_comparison.id

  depends_on = [
    aws_api_gateway_integration.lambda
  ]

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "prod" {
  deployment_id = aws_api_gateway_deployment.api.id
  rest_api_id   = aws_api_gateway_rest_api.price_comparison.id
  stage_name    = "prod"
}

# Lambda関数のAPI Gateway呼び出し許可（存在しない場合のみ作成）
resource "aws_lambda_permission" "api_gateway" {
  count = try(data.aws_lambda_function.existing_get_prices.function_name, "") != "" ? 0 : 1

  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = try(
    data.aws_lambda_function.existing_get_prices.function_name,
    try(aws_lambda_function.get_prices[0].function_name, "")
  )
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.price_comparison.execution_arn}/*/*"
}
