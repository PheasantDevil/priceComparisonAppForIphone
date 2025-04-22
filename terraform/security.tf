# AWS Security Hubの設定
resource "aws_securityhub_account" "main" {
  enable_default_standards = true
}

# Security Hubの標準を有効化
resource "aws_securityhub_standards_subscription" "cis" {
  standards_arn = "arn:aws:securityhub:::ruleset/cis-aws-foundations-benchmark/v/1.2.0"
  depends_on    = [aws_securityhub_account.main]
}

resource "aws_securityhub_standards_subscription" "pci" {
  standards_arn = "arn:aws:securityhub:::ruleset/pci-dss/v/3.2.1"
  depends_on    = [aws_securityhub_account.main]
}

# セキュリティイベントの監視
resource "aws_cloudwatch_event_rule" "security_events" {
  name        = "security-events"
  description = "セキュリティ関連のイベントを監視"

  event_pattern = jsonencode({
    source      = ["aws.securityhub"]
    detail-type = ["Security Hub Findings - Imported"]
  })
}

resource "aws_cloudwatch_event_target" "security_events" {
  rule      = aws_cloudwatch_event_rule.security_events.name
  target_id = "SecurityEvents"
  arn       = aws_sns_topic.alerts.arn
}

# セキュリティアラートの設定
resource "aws_cloudwatch_metric_alarm" "security_findings" {
  alarm_name          = "security-findings"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "SecurityFindings"
  namespace           = "AWS/SecurityHub"
  period              = "300"
  statistic           = "Sum"
  threshold           = "0"
  alarm_description   = "新しいセキュリティの検出結果があります"
  treat_missing_data  = "notBreaching"

  dimensions = {
    ProductName = "Security Hub"
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
}

# コンプライアンスチェックの設定
resource "aws_config_configuration_recorder" "main" {
  name     = "price-comparison-recorder"
  role_arn = aws_iam_role.config_role.arn
}

resource "aws_config_delivery_channel" "main" {
  name           = "price-comparison-delivery"
  s3_bucket_name = aws_s3_bucket.config_bucket.id
  depends_on     = [aws_config_configuration_recorder.main]
}

# 設定ファイル用のS3バケット
resource "aws_s3_bucket" "config_bucket" {
  bucket = "price-comparison-config-${var.environment}"
}

resource "aws_s3_bucket_acl" "config_bucket_acl" {
  bucket = aws_s3_bucket.config_bucket.id
  acl    = "private"
}

# ConfigのIAMロール
resource "aws_iam_role" "config_role" {
  name = "price-comparison-config-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "config.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "config_policy" {
  role       = aws_iam_role.config_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSConfigRole"
}

# WAF Web ACLの設定
resource "aws_wafv2_web_acl" "api_gateway" {
  name        = "api-gateway-waf"
  description = "WAF for API Gateway"
  scope       = "REGIONAL"

  default_action {
    allow {}
  }

  rule {
    name     = "RateLimit"
    priority = 1

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = 1000
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimit"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "SQLInjection"
    priority = 2

    action {
      block {}
    }

    statement {
      sqli_match_statement {
        field_to_match {
          query_string {}
        }
        text_transformation {
          priority = 1
          type     = "URL_DECODE"
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "SQLInjection"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "XSSProtection"
    priority = 3

    action {
      block {}
    }

    statement {
      xss_match_statement {
        field_to_match {
          query_string {}
        }
        text_transformation {
          priority = 1
          type     = "URL_DECODE"
        }
        text_transformation {
          priority = 2
          type     = "HTML_ENTITY_DECODE"
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "XSSProtection"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "SizeRestrictions"
    priority = 4

    action {
      block {}
    }

    statement {
      size_constraint_statement {
        field_to_match {
          query_string {}
        }
        comparison_operator = "GT"
        size                = 8192
        text_transformation {
          priority = 1
          type     = "URL_DECODE"
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "SizeRestrictions"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "CommonVulnerabilities"
    priority = 5

    action {
      block {}
    }

    statement {
      or_statement {
        statement {
          sqli_match_statement {
            field_to_match {
              body {}
            }
            text_transformation {
              priority = 1
              type     = "URL_DECODE"
            }
          }
        }
        statement {
          sqli_match_statement {
            field_to_match {
              uri_path {}
            }
            text_transformation {
              priority = 1
              type     = "URL_DECODE"
            }
          }
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "CommonVulnerabilities"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "WAF"
    sampled_requests_enabled   = true
  }
}

# WAFとAPI Gatewayの関連付け
resource "aws_wafv2_web_acl_association" "api_gateway" {
  resource_arn = aws_api_gateway_stage.production.arn
  web_acl_arn  = aws_wafv2_web_acl.api_gateway.arn
}

# セキュリティグループの設定
resource "aws_security_group" "lambda" {
  name        = "lambda-security-group"
  description = "Security group for Lambda functions"
  vpc_id      = var.vpc_id

  # API Gatewayからのインバウンドトラフィックを許可
  ingress {
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.api_gateway.id]
    description     = "Allow HTTPS traffic from API Gateway"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "lambda-security-group"
    Environment = var.environment
  }
}

# API Gateway用のセキュリティグループ
resource "aws_security_group" "api_gateway" {
  name        = "api-gateway-security-group"
  description = "Security group for API Gateway"
  vpc_id      = var.vpc_id

  # インターネットからのHTTPSアクセスを許可
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow HTTPS traffic from internet"
  }

  tags = {
    Name        = "api-gateway-security-group"
    Environment = var.environment
  }
}

# データ暗号化用のKMSキー
resource "aws_kms_key" "data_encryption" {
  description             = "KMS key for data encryption"
  deletion_window_in_days = 7
  enable_key_rotation     = true
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = "*"
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "kms:CallerAccount" = var.aws_account_id
          }
        }
      }
    ]
  })
}

# KMSキーのエイリアス
resource "aws_kms_alias" "data_encryption" {
  name          = "alias/data-encryption-key"
  target_key_id = aws_kms_key.data_encryption.key_id
}

# セキュリティ監査用のCloudTrail設定
resource "aws_cloudtrail" "security_audit" {
  name                          = "security-audit-trail"
  s3_bucket_name                = aws_s3_bucket.cloudtrail.id
  include_global_service_events = true
  is_multi_region_trail         = true
  enable_logging                = true

  event_selector {
    read_write_type           = "All"
    include_management_events = true
  }

  tags = {
    Environment = var.environment
    Purpose     = "SecurityAudit"
  }
}

# CloudTrail用のS3バケット
resource "aws_s3_bucket" "cloudtrail" {
  bucket        = "security-audit-trail-${var.aws_account_id}"
  force_destroy = true

  tags = {
    Environment = var.environment
    Purpose     = "SecurityAudit"
  }
}

# CloudTrail用のS3バケットポリシー
resource "aws_s3_bucket_policy" "cloudtrail" {
  bucket = aws_s3_bucket.cloudtrail.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "cloudtrail.amazonaws.com"
        }
        Action   = "s3:GetBucketAcl"
        Resource = aws_s3_bucket.cloudtrail.arn
      },
      {
        Effect = "Allow"
        Principal = {
          Service = "cloudtrail.amazonaws.com"
        }
        Action   = "s3:PutObject"
        Resource = "${aws_s3_bucket.cloudtrail.arn}/*"
        Condition = {
          StringEquals = {
            "s3:x-amz-acl" = "bucket-owner-full-control"
          }
        }
      }
    ]
  })
} 