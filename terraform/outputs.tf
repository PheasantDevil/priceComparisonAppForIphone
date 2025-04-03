output "api_gateway_url" {
  description = "The URL of the API Gateway"
  value       = "${aws_api_gateway_stage.prod.invoke_url}${aws_api_gateway_resource.get_prices.path}"
}
