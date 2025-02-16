output "api_gateway_url" {
  description = "API Gateway endpoint URL"
  value       = "${aws_api_gateway_stage.prod.invoke_url}/get_prices"
}

output "lambda_function_name" {
  description = "Lambda function name"
  value       = aws_lambda_function.get_prices.function_name
}
