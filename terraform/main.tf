terraform {
  required_version = ">= 1.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.31.0"
    }
  }
}

provider "aws" {
  region = "ap-northeast-1"
  
  # 本番環境ではこれらの設定を削除する
  skip_credentials_validation = false
  skip_metadata_api_check    = false
  skip_requesting_account_id = false

  max_retries = 10
  
  default_tags {
    tags = {
      Environment = "production"
      Project     = "iphone_price_tracker"
    }
  }
}

data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

# DynamoDBテーブル
resource "aws_dynamodb_table" "iphone_prices" {
  name           = "iphone_prices"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "id"
  range_key      = "timestamp"

  attribute {
    name = "id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  global_secondary_index {
    name               = "TimestampIndex"
    hash_key           = "timestamp"
    projection_type    = "ALL"
    write_capacity     = 0
    read_capacity      = 0
  }

  tags = {
    Environment = "production"
    Project     = "iphone_price_tracker"
  }

  lifecycle {
    ignore_changes = [
      read_capacity,
      write_capacity
    ]
  }
}

resource "aws_dynamodb_table" "official_prices" {
  name         = "official_prices"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "series"
  range_key    = "capacity"

  attribute {
    name = "series"
    type = "S"
  }

  attribute {
    name = "capacity"
    type = "S"
  }

  global_secondary_index {
    name            = "CapacityIndex"
    hash_key        = "series"
    range_key       = "capacity"
    projection_type = "ALL"
  }

  tags = {
    Environment = "production"
    Project     = "iphone_price_tracker"
  }

  lifecycle {
    ignore_changes = [
      read_capacity,
      write_capacity
    ]
  }
}
