# Lambda実行用のIAMロール
resource "aws_iam_role" "lambda_execution_role" {
  name = "lambda_execution_role"

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

  tags = {
    Name        = "lambda_execution_role"
    Environment = "production"
    Project     = "iphone_price_tracker"
  }
}

# Lambda実行用のIAMポリシー
resource "aws_iam_role_policy" "dynamodb_access" {
  name = "dynamodb_access"
  role = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:BatchGetItem",
          "dynamodb:BatchWriteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          aws_dynamodb_table.kaitori_prices.arn,
          aws_dynamodb_table.official_prices.arn,
          aws_dynamodb_table.price_history.arn
        ]
      }
    ]
  })
}

# Lambda実行用のIAMポリシー（SQS）
resource "aws_iam_role_policy" "lambda_sqs_policy" {
  name = "lambda_sqs_policy"
  role = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = aws_sqs_queue.lambda_dlq.arn
      }
    ]
  })
}

# Lambda実行用のIAMポリシー（CloudWatch Logs）
resource "aws_iam_role_policy_attachment" "lambda_execution_basic" {
  role       = aws_iam_role.lambda_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Lambda実行用のIAMポリシー（DynamoDB）
resource "aws_iam_role_policy" "price_history_dynamodb_policy" {
  name = "price_history_dynamodb_policy"
  role = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:BatchGetItem",
          "dynamodb:BatchWriteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          aws_dynamodb_table.kaitori_prices.arn,
          aws_dynamodb_table.official_prices.arn,
          aws_dynamodb_table.price_history.arn
        ]
      }
    ]
  })
}

# GitHub Actions用のIAMロール
resource "aws_iam_role" "github_actions" {
  name = "github-actions-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRoleWithWebIdentity"
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.github_actions.arn
        }
        Condition = {
          StringLike = {
            "token.actions.githubusercontent.com:sub" = "repo:${var.github_org}/${var.github_repo}:*"
          }
        }
      }
    ]
  })
}

# GitHub Actions用のIAMポリシー
resource "aws_iam_role_policy" "github_actions_terraform" {
  name = "github_actions_terraform"
  role = aws_iam_role.github_actions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:*",
          "lambda:*",
          "apigateway:*",
          "cloudwatch:*",
          "logs:*",
          "iam:*",
          "s3:*",
          "sns:*",
          "sqs:*",
          "kms:*"
        ]
        Resource = "*"
      }
    ]
  })
}

# GitHub Actions用のOIDCプロバイダー
resource "aws_iam_openid_connect_provider" "github_actions" {
  url = "https://token.actions.githubusercontent.com"

  client_id_list = [
    "sts.amazonaws.com"
  ]

  thumbprint_list = [
    "6938fd4d98bab03faadb97b34396831e3780aea1"
  ]
}

# スモークテスト用のIAMロール
resource "aws_iam_role" "smoke_test" {
  name = "smoke-test-role"

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

  tags = {
    Name        = "smoke-test-role"
    Environment = "production"
    Project     = "iphone_price_tracker"
  }
}

# スモークテスト用のIAMポリシー
resource "aws_iam_role_policy" "smoke_test_policy" {
  name = "smoke_test_policy"
  role = aws_iam_role.smoke_test.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          aws_dynamodb_table.kaitori_prices.arn,
          aws_dynamodb_table.official_prices.arn,
          aws_dynamodb_table.price_history.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# スモークテスト用のIAMポリシー（CloudWatch Logs）
resource "aws_iam_role_policy_attachment" "smoke_test_basic" {
  role       = aws_iam_role.smoke_test.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# デプロイメント検証用のIAMロール
resource "aws_iam_role" "deployment_verification" {
  name = "deployment-verification-role"

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

  tags = {
    Name        = "deployment-verification-role"
    Environment = "production"
    Project     = "iphone_price_tracker"
  }
}

# デプロイメント検証用のIAMポリシー
resource "aws_iam_role_policy" "deployment_verification_policy" {
  name = "deployment_verification_policy"
  role = aws_iam_role.deployment_verification.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:GetFunction",
          "lambda:GetFunctionConfiguration",
          "lambda:ListVersionsByFunction",
          "lambda:GetAlias",
          "lambda:GetPolicy"
        ]
        Resource = aws_lambda_function.get_prices.arn
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:DescribeTable",
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          aws_dynamodb_table.kaitori_prices.arn,
          aws_dynamodb_table.official_prices.arn,
          aws_dynamodb_table.price_history.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "apigateway:GET"
        ]
        Resource = "arn:aws:apigateway:${var.aws_region}::/restapis/${aws_api_gateway_rest_api.price_comparison.id}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
} 