terraform {
  required_providers {
    render = {
      source  = "render/render"
      version = "~> 0.3"
    }
  }

  backend "local" {
    path = "terraform.tfstate"  # 状態管理ファイル
  }
}

provider "render" {
  api_key = var.render_api_key
}

# PostgreSQLデータベースの作成
resource "render_postgresql" "price-comparison-app" {
  name     = var.db_name
  database = var.db_name
  user     = var.db_user
  password = var.db_password
  region   = var.db_region
  version  = var.db_version
}

# 出力変数で接続情報を確認
output "database_url" {
  value = render_postgresql.price-comparison-app.connection_string
}
