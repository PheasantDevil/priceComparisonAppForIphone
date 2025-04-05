output "api_gateway_url" {
  description = "API Gateway endpoint URL"
  value       = "${aws_api_gateway_stage.prod.invoke_url}/${aws_api_gateway_resource.prices.path_part}"
}

output "dynamodb_table_arn" {
  value = aws_dynamodb_table.iphone_prices.arn
}

output "official_prices_table_arn" {
  value = aws_dynamodb_table.official_prices.arn
}

output "lambda_function_name" {
  value = aws_lambda_function.get_prices.function_name
}

output "lambda_function_arn" {
  value = aws_lambda_function.get_prices.arn
}

output "lambda_role_arn" {
  value = aws_iam_role.lambda_role.arn
}
