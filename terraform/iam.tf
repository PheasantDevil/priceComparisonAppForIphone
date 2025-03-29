# terraform/iam.tf
# 既存のIAMロールを確認
data "aws_iam_role" "existing_lambda_role" {
  count = 1
  name  = "get_prices_lambda_role"
}

# Lambda実行用のIAMロール（存在しない場合のみ作成）
resource "aws_iam_role" "lambda_role" {
  count = try(data.aws_iam_role.existing_lambda_role[0].name, "") == "" ? 1 : 0

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
  lambda_role_name = try(data.aws_iam_role.existing_lambda_role[0].name, "")
  lambda_role_id   = try(data.aws_iam_role.existing_lambda_role[0].id, "")
  is_new_role      = try(data.aws_iam_role.existing_lambda_role[0].name, "") == ""
}

# 基本的なLambda実行権限
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  count = try(data.aws_iam_role.existing_lambda_role[0].name, "") == "" ? 1 : 0

  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.lambda_role[0].name
}

# DynamoDB アクセス用のポリシー
resource "aws_iam_role_policy" "dynamodb_access" {
  count = try(data.aws_iam_role.existing_lambda_role[0].name, "") == "" ? 1 : 0

  name = "dynamodb_access"
  role = aws_iam_role.lambda_role[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem"
        ]
        Resource = [
          try(data.aws_dynamodb_table.iphone_prices[0].arn, aws_dynamodb_table.iphone_prices[0].arn)
        ]
      }
    ]
  })
}

# IAMロールのARNを出力（既存または新規作成）
output "lambda_role_arn" {
  value = try(data.aws_iam_role.existing_lambda_role[0].arn, aws_iam_role.lambda_role[0].arn)
}
