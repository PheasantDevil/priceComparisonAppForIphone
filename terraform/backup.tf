# DynamoDBのバックアップ設定
resource "aws_backup_plan" "dynamodb_backup" {
  name = "dynamodb-backup-plan"

  rule {
    rule_name         = "daily-backup"
    target_vault_name = aws_backup_vault.dynamodb_backup.name
    schedule          = "cron(0 3 ? * * *)" # 毎日午前3時

    lifecycle {
      delete_after = 30 # 30日間保持
    }
  }
}

# バックアップボールト
resource "aws_backup_vault" "dynamodb_backup" {
  name        = "dynamodb-backup-vault"
  kms_key_arn = aws_kms_key.backup.arn
}

# バックアップ用KMSキー
resource "aws_kms_key" "backup" {
  description             = "KMS key for DynamoDB backups"
  deletion_window_in_days = 7
  enable_key_rotation     = true
}

# バックアップポリシー
resource "aws_backup_selection" "dynamodb" {
  name         = "dynamodb-backup"
  plan_id      = aws_backup_plan.dynamodb_backup.id
  iam_role_arn = aws_iam_role.backup.arn

  resources = [
    aws_dynamodb_table.kaitori_prices.arn,
    aws_dynamodb_table.official_prices.arn,
    aws_dynamodb_table.price_history.arn
  ]

  selection_tag {
    type  = "STRINGEQUALS"
    key   = "Environment"
    value = "production"
  }
}

# バックアップ用IAMロール
resource "aws_iam_role" "backup" {
  name = "backup-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "backup.amazonaws.com"
        }
      }
    ]
  })
}

# バックアップ用IAMポリシー
resource "aws_iam_role_policy" "backup" {
  name = "backup-policy"
  role = aws_iam_role.backup.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:DescribeTable",
          "dynamodb:ListBackups",
          "dynamodb:CreateBackup",
          "dynamodb:DeleteBackup",
          "dynamodb:RestoreTableFromBackup"
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
          "tag:GetResources"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ]
        Resource = aws_kms_key.backup.arn
      }
    ]
  })
} 