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

# ===============================
# Monitoring & Reliability Outputs
# ===============================

output "sns_alerts_topic_arn" {
  description = "ARN of the SNS topic for pipeline alerts"
  value       = aws_sns_topic.alerts.arn
}

output "sns_alerts_subscription_email" {
  description = "Email endpoint subscribed to SNS alerts"
  value       = aws_sns_topic_subscription.email_alert.endpoint
}

output "redshift_cluster_identifier" {
  description = "Identifier of the Redshift cluster"
  value       = aws_redshift_cluster.main.cluster_identifier
}

output "redshift_cluster_arn" {
  description = "ARN of the Redshift cluster"
  value       = aws_redshift_cluster.main.arn
}

output "redshift_query_failures_alarm_name" {
  description = "CloudWatch alarm name monitoring Redshift query failures"
  value       = aws_cloudwatch_metric_alarm.redshift_query_failures.alarm_name
}

output "redshift_high_cpu_alarm_name" {
  description = "CloudWatch alarm name monitoring Redshift CPU utilization"
  value       = aws_cloudwatch_metric_alarm.redshift_high_cpu.alarm_name
}

output "s3_4xx_error_alarm_name" {
  description = "CloudWatch alarm name monitoring S3 4xx errors"
  value       = aws_cloudwatch_metric_alarm.s3_4xx_errors.alarm_name
}

output "s3_5xx_error_alarm_name" {
  description = "CloudWatch alarm name monitoring S3 5xx errors"
  value       = aws_cloudwatch_metric_alarm.s3_5xx_errors.alarm_name
}

# ===============================
# EMR & Lambda Monitoring Outputs
# ===============================

output "emr_step_failures_alarm_name" {
  description = "CloudWatch alarm name monitoring EMR failed steps"
  value       = aws_cloudwatch_metric_alarm.emr_step_failures.alarm_name
}

output "lambda_errors_alarm_name" {
  description = "CloudWatch alarm name monitoring Lambda errors"
  value       = aws_cloudwatch_metric_alarm.lambda_errors.alarm_name
}
