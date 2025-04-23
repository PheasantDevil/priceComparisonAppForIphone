output "api_gateway_url" {
  description = "API GatewayのエンドポイントURL"
  value       = "${aws_api_gateway_stage.production.invoke_url}/${aws_api_gateway_resource.prices.path_part}"
}

output "dynamodb_table_name" {
  description = "DynamoDBテーブルの名前"
  value       = aws_dynamodb_table.price_comparison.name
}

output "lambda_function_name" {
  description = "Lambda関数の名前"
  value       = aws_lambda_function.get_prices.function_name
}

output "lambda_execution_role_arn" {
  description = "ARN of the Lambda execution role"
  value       = aws_iam_role.lambda_execution_role.arn
}

output "dynamodb_table_arn" {
  value = aws_dynamodb_table.iphone_prices.arn
}

output "official_prices_table_arn" {
  value = aws_dynamodb_table.official_prices.arn
}

output "lambda_function_arn" {
  value = aws_lambda_function.get_prices.arn
}

output "lambda_role_arn" {
  description = "ARN of the Lambda role"
  value       = aws_iam_role.lambda_execution_role.arn
}
