variable "render_api_key" {
  description = "Render API key for authentication"
  type        = string
}

variable "db_name" {
  default = "price-comparison-app"
  description = "The name of the PostgreSQL database"
}

variable "db_user" {
  default = "app_user"
  description = "The username for the PostgreSQL database"
}

variable "db_password" {
  description = "The password for the PostgreSQL user"
  type        = string
}

variable "db_region" {
  default = "oregon"
  description = "The region where the database will be hosted"
}

variable "db_version" {
  default = "16"
  description = "The PostgreSQL version"
}
