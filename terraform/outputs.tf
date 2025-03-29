output "api_gateway_url" {
  description = "API Gateway endpoint URL"
  value       = "${aws_api_gateway_stage.prod.invoke_url}/get_prices"
}
