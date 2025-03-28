terraform {
  required_version = ">= 1.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.92.0"
    }
  }
}

provider "aws" {
  region = "ap-northeast-1"
}

# 既存のDynamoDBテーブルを確認
data "aws_dynamodb_table" "iphone_prices" {
  name = "iphone_prices"
}

data "aws_dynamodb_table" "official_prices" {
  name = "official_prices"
}

# DynamoDBテーブル（存在しない場合のみ作成）
resource "aws_dynamodb_table" "iphone_prices" {
  count = try(data.aws_dynamodb_table.iphone_prices.name, "") == "" ? 1 : 0

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
    hash_key           = "id"
    range_key          = "timestamp"
    projection_type    = "ALL"
    write_capacity     = 5
    read_capacity      = 5
  }

  tags = {
    Environment = "production"
  }
}

resource "aws_dynamodb_table" "official_prices" {
  count = try(data.aws_dynamodb_table.official_prices.name, "") == "" ? 1 : 0

  name           = "official_prices"
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
    hash_key           = "id"
    range_key          = "timestamp"
    projection_type    = "ALL"
    write_capacity     = 5
    read_capacity      = 5
  }

  tags = {
    Environment = "production"
  }
}

# DynamoDBテーブルのARNを出力
output "dynamodb_table_arn" {
  value = try(data.aws_dynamodb_table.iphone_prices.arn, "")
}
