resource "render_postgresql" "price-comparison-app" {
  name     = var.db_name
  database = var.db_name
  user     = var.db_user
  password = var.db_password
  region   = var.db_region
  version  = var.db_version
}

output "database_url" {
  value = render_postgresql.price-comparison-app.connection_string
}
