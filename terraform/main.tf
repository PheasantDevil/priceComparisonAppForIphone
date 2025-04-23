terraform {
  required_version = ">= 1.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.31.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "2.4.2"
    }
  }
}

# AWSプロバイダーの設定
provider "aws" {
  region = "ap-northeast-1"

  default_tags {
    tags = {
      Environment = "production"
      Project     = "iphone_price_tracker"
    }
  }
}

provider "archive" {}

# 現在のAWSアカウントIDを取得
data "aws_caller_identity" "current" {}

# 現在のリージョンを取得
data "aws_region" "current" {} 