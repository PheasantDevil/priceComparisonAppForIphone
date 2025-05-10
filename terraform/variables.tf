variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "project" {
  description = "Project name"
  type        = string
  default     = "iphone_price_tracker"
}

variable "alert_email" {
  description = "アラート通知を受け取るメールアドレス"
  type        = string
}

variable "vpc_id" {
  description = "The ID of the VPC where resources will be deployed"
  type        = string
}

variable "aws_account_id" {
  description = "The AWS account ID"
  type        = string
}

variable "budget_notification_email" {
  description = "Email address for budget notifications"
  type        = string
}

variable "github_org" {
  description = "GitHub organization name"
  type        = string
  default     = "PheasantDevil"
}

variable "github_repo" {
  description = "GitHub repository name"
  type        = string
  default     = "priceComparisonAppForIphone"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-northeast-1"
}

variable "line_channel_access_token" {
  description = "LINE Messaging API channel access token"
  type        = string
  sensitive   = true
}

variable "line_notify_token" {
  description = "LINE Notifyのアクセストークン"
  type        = string
  sensitive   = true
}

variable "create_sample_data" {
  description = "サンプルデータを作成するかどうか"
  type        = bool
  default     = false
}

variable "skip_organization_policy" {
  description = "Whether to skip organization policy checks"
  type        = bool
  default     = false
}

variable "evaluation_periods" {
  description = "Number of evaluation periods for CloudWatch alarms"
  type        = number
  default     = 2
}

variable "period" {
  description = "Period in seconds for CloudWatch metrics"
  type        = number
  default     = 300
}
