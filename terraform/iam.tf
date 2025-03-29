# terraform/iam.tf
# 既存のIAMロールを確認
data "aws_iam_role" "existing_lambda_role" {
  name = "get_prices_lambda_role"
}

# IAMロール（存在しない場合のみ作成）
resource "aws_iam_role" "lambda_role" {
  count = try(data.aws_iam_role.existing_lambda_role.name, "") == "" ? 1 : 0

  name = "get_prices_lambda_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# ロール名の取得（既存または新規作成）
locals {
  lambda_role_name = try(data.aws_iam_role.existing_lambda_role.name, "")
  lambda_role_id   = try(data.aws_iam_role.existing_lambda_role.id, "")
  is_new_role      = try(data.aws_iam_role.existing_lambda_role.name, "") == ""
}

# 基本的なLambda実行権限
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  count = try(data.aws_iam_role.existing_lambda_role.name, "") == "" ? 1 : 0

  role       = try(data.aws_iam_role.existing_lambda_role.name, aws_iam_role.lambda_role[0].name)
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# DynamoDBアクセスポリシー
resource "aws_iam_role_policy" "dynamodb_access" {
  count = try(data.aws_iam_role.existing_lambda_role.name, "") == "" ? 1 : 0

  name = "dynamodb_access"
  role = try(data.aws_iam_role.existing_lambda_role.name, aws_iam_role.lambda_role[0].name)

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          try(data.aws_dynamodb_table.iphone_prices.arn, aws_dynamodb_table.iphone_prices[0].arn),
          try(data.aws_dynamodb_table.official_prices.arn, aws_dynamodb_table.official_prices[0].arn)
        ]
      }
    ]
  })
}

# IAMロールのARNを出力
output "lambda_role_arn" {
  value = try(data.aws_iam_role.existing_lambda_role.arn, "")
}
