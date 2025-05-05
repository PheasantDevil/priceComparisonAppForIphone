provider "aws" {
  region = "ap-northeast-1"

  default_tags {
    tags = {
      Environment = "production"
      Project     = "iphone_price_tracker"
    }
  }
} 