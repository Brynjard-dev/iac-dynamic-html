variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "dynamic-html"
}

variable "default_string" {
  description = "Initial value for the dynamic string"
  type        = string
  default     = "Hello, World!"
}
