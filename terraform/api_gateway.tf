# CloudWatch Log Group is already defined in monitoring.tf
# resource "aws_cloudwatch_log_group" "api_gateway" {
#   name              = "/aws/apigateway/price-comparison-api"
#   retention_in_days = 30
#   tags = {
#     Name        = "api-gateway-logs"
#     Environment = "production"
#     Project     = "iphone_price_tracker"
#   }
# }

# HTTP API Gateway
resource "aws_apigatewayv2_api" "main" {
  name          = "price-comparison-http-api"
  protocol_type = "HTTP"
  description   = "HTTP API for iPhone price comparison"
}

# API Gateway Stage
resource "aws_api_gateway_stage" "production" {
  deployment_id = aws_api_gateway_deployment.price_comparison.id
  rest_api_id   = aws_api_gateway_rest_api.price_comparison.id
  stage_name    = "production"

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway_logs.arn
    format         = jsonencode({
      requestId               = "$context.requestId"
      sourceIp               = "$context.identity.sourceIp"
      requestTime            = "$context.requestTime"
      protocol              = "$context.protocol"
      httpMethod            = "$context.httpMethod"
      resourcePath          = "$context.resourcePath"
      routeKey              = "$context.routeKey"
      status                = "$context.status"
      responseLength        = "$context.responseLength"
      integrationErrorMessage = "$context.integrationErrorMessage"
    })
  }

  xray_tracing_enabled = true

  depends_on = [
    aws_api_gateway_deployment.price_comparison
  ]
}

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

# CORS設定の追加
resource "aws_api_gateway_method" "get_prices_options" {
  rest_api_id   = aws_api_gateway_rest_api.price_comparison.id
  resource_id   = aws_api_gateway_resource.prices.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_method_response" "get_prices_options_200" {
  rest_api_id = aws_api_gateway_rest_api.price_comparison.id
  resource_id = aws_api_gateway_resource.prices.id
  http_method = aws_api_gateway_method.get_prices_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration" "get_prices_options_integration" {
  rest_api_id = aws_api_gateway_rest_api.price_comparison.id
  resource_id = aws_api_gateway_resource.prices.id
  http_method = aws_api_gateway_method.get_prices_options.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_integration_response" "get_prices_options_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.price_comparison.id
  resource_id = aws_api_gateway_resource.prices.id
  http_method = aws_api_gateway_method.get_prices_options.http_method
  status_code = aws_api_gateway_method_response.get_prices_options_200.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

resource "aws_api_gateway_integration" "lambda" {
  rest_api_id = aws_api_gateway_rest_api.price_comparison.id
  resource_id = aws_api_gateway_resource.prices.id
  http_method = aws_api_gateway_method.get_prices.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.get_prices.invoke_arn
}

resource "aws_api_gateway_deployment" "price_comparison" {
  rest_api_id = aws_api_gateway_rest_api.price_comparison.id

  depends_on = [
    aws_api_gateway_integration.lambda
  ]

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "prod" {
  deployment_id = aws_api_gateway_deployment.price_comparison.id
  rest_api_id   = aws_api_gateway_rest_api.price_comparison.id
  stage_name    = "prod"
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_prices.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.price_comparison.execution_arn}/*/*"
}

resource "aws_api_gateway_resource" "price_history" {
  rest_api_id = aws_api_gateway_rest_api.price_comparison.id
  parent_id   = aws_api_gateway_rest_api.price_comparison.root_resource_id
  path_part   = "price-history"
}

resource "aws_api_gateway_method" "price_history_get" {
  rest_api_id   = aws_api_gateway_rest_api.price_comparison.id
  resource_id   = aws_api_gateway_resource.price_history.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "price_history_integration" {
  rest_api_id             = aws_api_gateway_rest_api.price_comparison.id
  resource_id             = aws_api_gateway_resource.price_history.id
  http_method             = aws_api_gateway_method.price_history_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.get_price_history.invoke_arn
}

resource "aws_lambda_permission" "api_gateway_price_history" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_price_history.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.price_comparison.execution_arn}/*/*"
}

resource "aws_apigatewayv2_route" "predict_prices" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /predict-prices"
  target    = "integrations/${aws_apigatewayv2_integration.predict_prices.id}"
}

resource "aws_apigatewayv2_integration" "predict_prices" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"

  connection_type    = "INTERNET"
  description        = "Predict prices integration"
  integration_method = "POST"
  integration_uri    = aws_lambda_function.predict_prices_lambda.invoke_arn
}

resource "aws_apigatewayv2_route" "compare_prices" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /compare-prices"
  target    = "integrations/${aws_apigatewayv2_integration.compare_prices.id}"
}

resource "aws_apigatewayv2_integration" "compare_prices" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"

  connection_type    = "INTERNET"
  description        = "Compare prices integration"
  integration_method = "POST"
  integration_uri    = aws_lambda_function.compare_prices_lambda.invoke_arn
}

resource "aws_apigatewayv2_route" "line_notification" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /line-notification"
  target    = "integrations/${aws_apigatewayv2_integration.line_notification.id}"
}

resource "aws_apigatewayv2_integration" "line_notification" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"

  connection_type    = "INTERNET"
  description        = "LINE notification integration"
  integration_method = "POST"
  integration_uri    = aws_lambda_function.line_notification_lambda.invoke_arn
}
