# S3 Outputs
output "s3_bucket_name" {
  description = "The name of the raw data S3 bucket"
  value       = aws_s3_bucket.raw_data.bucket
}

# Redshift Outputs
output "redshift_endpoint" {
  description = "The endpoint of the Redshift cluster"
  value       = aws_redshift_cluster.main.endpoint
}

output "redshift_username" {
  description = "The master username for the Redshift cluster"
  value       = aws_redshift_cluster.main.master_username
  sensitive   = true
}

output "redshift_database" {
  description = "The default database name for Redshift"
  value       = aws_redshift_cluster.main.database_name
}

output "redshift_role_arn" {
  description = "IAM Role ARN attached to Redshift for S3 access"
  value       = aws_iam_role.redshift_role.arn
}
