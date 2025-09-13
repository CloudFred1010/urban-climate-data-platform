# ===============================
# S3 Outputs
# ===============================
output "s3_bucket_name" {
  description = "Name of the raw data S3 bucket"
  value       = aws_s3_bucket.raw_data.bucket
}

output "s3_raw_prefixes" {
  description = "Standard prefixes for raw data organisation in S3"
  value = {
    weather      = "${aws_s3_bucket.raw_data.bucket}/raw/weather/"
    demographics = "${aws_s3_bucket.raw_data.bucket}/raw/demographics/"
    geospatial   = "${aws_s3_bucket.raw_data.bucket}/raw/geospatial/"
  }
}

# ===============================
# Redshift Outputs
# ===============================
output "redshift_endpoint" {
  description = "Endpoint of the Redshift cluster"
  value       = aws_redshift_cluster.main.endpoint
  sensitive   = true
}

output "redshift_username" {
  description = "Master username for the Redshift cluster"
  value       = aws_redshift_cluster.main.master_username
  sensitive   = true
}

output "redshift_database" {
  description = "Default database name for Redshift"
  value       = aws_redshift_cluster.main.database_name
}

output "redshift_role_arn" {
  description = "IAM Role ARN attached to Redshift for S3 access"
  value       = aws_iam_role.redshift_role.arn
}

output "redshift_password_secret_arn" {
  description = "Secrets Manager ARN storing the Redshift admin password"
  value       = aws_secretsmanager_secret.redshift_password.arn
}
