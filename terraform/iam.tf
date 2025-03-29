# terraform/iam.tf
# 既存のIAMロールの存在確認
data "aws_iam_role" "existing_lambda_role" {
  name = "get_prices_lambda_role"
}

# Lambda実行用のIAMロール（存在しない場合のみ作成）
resource "aws_iam_role" "lambda_role" {
  # 既存のロールが見つからない場合のみ作成
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

  lifecycle {
    prevent_destroy = true  # 誤削除防止
  }
}

# 基本的なLambda実行権限
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = try(
    data.aws_iam_role.existing_lambda_role.name,
    try(aws_iam_role.lambda_role[0].name, "")
  )

  count = try(data.aws_iam_role.existing_lambda_role.name, "") != "" ? 1 : 0
}

# DynamoDB アクセス用のポリシー
resource "aws_iam_role_policy" "dynamodb_access" {
  name = "dynamodb_access"
  role = try(
    data.aws_iam_role.existing_lambda_role.id,
    try(aws_iam_role.lambda_role[0].id, "")
  )

  count = try(data.aws_iam_role.existing_lambda_role.name, "") != "" ? 1 : 0

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
          data.aws_dynamodb_table.iphone_prices.arn
        ]
      }
    ]
  })
}

# IAMロールのARNを出力（既存または新規作成）
output "lambda_role_arn" {
  value = try(
    data.aws_iam_role.existing_lambda_role.arn,
    try(aws_iam_role.lambda_role[0].arn, "")
  )
}
