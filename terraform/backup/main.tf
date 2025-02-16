terraform {
  required_version = ">= 1.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # バックエンド設定は後で追加
  # backend "s3" { ... }
}

provider "aws" {
  region = "ap-northeast-1"
}

# DynamoDBテーブルの定義のみを残す
resource "aws_dynamodb_table" "iphone_prices" {
  name           = "iphone_prices"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "series"
  range_key      = "capacity"

  attribute {
    name = "series"
    type = "S"
  }

  attribute {
    name = "capacity"
    type = "S"
  }

  tags = {
    Environment = "production"
    Project     = "price-comparison"
  }
}

resource "aws_dynamodb_table" "official_prices" {
  name           = "official_prices"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "series"
  range_key      = "capacity"

  attribute {
    name = "series"
    type = "S"
  }

  attribute {
    name = "capacity"
    type = "S"
  }

  tags = {
    Environment = "production"
    Project     = "price-comparison"
  }
}
