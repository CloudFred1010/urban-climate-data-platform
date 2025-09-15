output "redshift_endpoint" {
  value       = module.redshift.redshift_endpoint
  description = "Endpoint of the Redshift cluster"
}

output "redshift_database" {
  value       = module.redshift.redshift_database
  description = "Database name for Redshift"
}

output "redshift_role_arn" {
  value       = module.redshift.redshift_role_arn
  description = "IAM role ARN attached to Redshift"
}

output "redshift_cluster_id" {
  value       = module.redshift.redshift_cluster_id
  description = "Redshift cluster identifier"
}

output "redshift_cluster_arn" {
  value       = module.redshift.redshift_cluster_arn
  description = "Redshift cluster ARN"
}
