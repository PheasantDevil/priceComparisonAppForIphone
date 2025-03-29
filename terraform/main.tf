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

# 既存のテーブルの存在確認
data "aws_dynamodb_table" "existing_iphone_prices" {
  name = "iphone_prices"
}

data "aws_dynamodb_table" "existing_official_prices" {
  name = "official_prices"
}

# テーブルが存在しない場合のみ作成
resource "aws_dynamodb_table" "iphone_prices" {
  count = try(data.aws_dynamodb_table.existing_iphone_prices.name, "") == "" ? 1 : 0

  name         = "iphone_prices"
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

  lifecycle {
    prevent_destroy = true
    ignore_changes = [
      read_capacity,
      write_capacity,
      range_key
    ]
  }
}

resource "aws_dynamodb_table" "official_prices" {
  count = try(data.aws_dynamodb_table.existing_official_prices.name, "") == "" ? 1 : 0

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

  lifecycle {
    prevent_destroy = true
    ignore_changes = [
      read_capacity,
      write_capacity,
      range_key
    ]
  }
}

# DynamoDBテーブルの参照
data "aws_dynamodb_table" "iphone_prices" {
  name = "iphone_prices"
}

data "aws_dynamodb_table" "official_prices" {
  name = "official_prices"
}

# テーブルのARNを出力（既存または新規作成）
output "dynamodb_table_arn" {
  value = try(
    data.aws_dynamodb_table.existing_iphone_prices.arn,
    try(aws_dynamodb_table.iphone_prices[0].arn, "")
  )
}
