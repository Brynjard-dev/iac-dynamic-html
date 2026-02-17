output "api_url" {
  description = "URL of the HTML page"
  value       = aws_apigatewayv2_stage.default.invoke_url
}

output "ssm_parameter_name" {
  description = "SSM parameter name for updating the dynamic string"
  value       = aws_ssm_parameter.dynamic_string.name
}
