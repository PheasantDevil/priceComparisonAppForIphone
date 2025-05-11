# AWS Security Hubの設定
resource "aws_securityhub_account" "main" {
}

# Security Hubの標準を有効化
resource "aws_securityhub_standards_subscription" "cis" {
  standards_arn = "arn:aws:securityhub:::ruleset/cis-aws-foundations-benchmark/v/1.2.0"
  depends_on    = [aws_securityhub_account.main]
}

resource "aws_securityhub_standards_subscription" "pci" {
  standards_arn = "arn:aws:securityhub:ap-northeast-1::standards/pci-dss/v/3.2.1"
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

  tags = {
    Name        = "api-gateway-waf"
    Environment = "production"
    Project     = "iphone_price_tracker"
  }
}

resource "aws_wafv2_web_acl_association" "api_gateway" {
  resource_arn = aws_api_gateway_stage.production.arn
  web_acl_arn  = aws_wafv2_web_acl.api_gateway.arn

  depends_on = [
    aws_api_gateway_stage.production,
    aws_wafv2_web_acl.api_gateway
  ]
}

# KMSキーの設定
resource "aws_kms_key" "data_encryption" {
  description             = "KMS key for data encryption"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      }
    ]
  })

  tags = {
    Name        = "data-encryption-key"
    Environment = "production"
    Project     = "iphone_price_tracker"
  }
}

# KMSキーのエイリアス
resource "aws_kms_alias" "data_encryption" {
  name          = "alias/data-encryption-key"
  target_key_id = aws_kms_key.data_encryption.key_id
}

provider "aws" {
  alias  = "ap-southeast-1"
  region = "ap-southeast-1"
}

resource "aws_kms_key" "data_encryption_replica" {
  provider            = aws.ap-southeast-1
  description         = "KMS key for encrypting DynamoDB data in ap-southeast-1"
  enable_key_rotation = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::273354647319:root"
        }
        Action   = "kms:*"
        Resource = "*"
      }
    ]
  })

  tags = {
    Name        = "data-encryption-key-replica"
    Environment = "production"
    Project     = "iphone_price_tracker"
  }
}

resource "aws_kms_alias" "data_encryption_replica" {
  provider      = aws.ap-southeast-1
  name          = "alias/data-encryption-key-replica"
  target_key_id = aws_kms_key.data_encryption_replica.key_id
} 