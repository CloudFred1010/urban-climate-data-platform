variable "redshift_password" {
  description = "Master password for Redshift cluster in this environment"
  type        = string
  sensitive   = true
}
