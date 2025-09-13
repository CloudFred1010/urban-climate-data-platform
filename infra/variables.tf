# ===============================
# Core Variables
# ===============================

# AWS region for all resources
variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "eu-west-2"
}

# Master username for Redshift
variable "redshift_username" {
  description = "Master username for the Redshift cluster"
  type        = string

  # Do not hardcode sensitive values in Terraform code.
  # Default is provided for convenience in non-prod.
  default = "admin"
}

# Master password for Redshift (must be passed in via GitHub Actions secret)
variable "redshift_password" {
  description = "Master password for the Redshift cluster (sensitive)"
  type        = string
  sensitive   = true
}

# Redshift instance type
variable "redshift_node_type" {
  description = "Instance type for Redshift cluster nodes"
  type        = string
  default     = "ra3.large"
}

# Number of Redshift cluster nodes
variable "redshift_nodes" {
  description = "Number of nodes in the Redshift cluster"
  type        = number
  default     = 2
}

# ===============================
# Monitoring & Reliability
# ===============================

# Email address to subscribe to SNS alerts
variable "alert_email" {
  description = "Email address for receiving pipeline alerts"
  type        = string
  default     = "your_email@example.com"
}

# CloudWatch alarm threshold for Redshift query failures
variable "redshift_query_failure_threshold" {
  description = "Number of failed Redshift queries that will trigger an alarm"
  type        = number
  default     = 0
}

# CloudWatch evaluation period (in seconds)
variable "cloudwatch_evaluation_period" {
  description = "Evaluation period for CloudWatch alarms in seconds"
  type        = number
  default     = 300
}

# Redshift high CPU utilization threshold
variable "redshift_high_cpu_threshold" {
  description = "CPU utilization percentage that will trigger a high CPU alarm for Redshift"
  type        = number
  default     = 80
}

# S3 4xx error threshold
variable "s3_4xx_error_threshold" {
  description = "Number of 4xx errors on the S3 bucket that will trigger an alarm"
  type        = number
  default     = 10
}

# S3 5xx error threshold
variable "s3_5xx_error_threshold" {
  description = "Number of 5xx errors on the S3 bucket that will trigger an alarm"
  type        = number
  default     = 1
}

# EMR cluster JobFlowId (placeholder until EMR is deployed)
variable "emr_cluster_id" {
  description = "JobFlowId of the EMR cluster to monitor (set once EMR is deployed)"
  type        = string
  default     = "j-XXXXXXXXXXXXX"
}

# Lambda function name (placeholder until Lambda is deployed)
variable "lambda_function_name" {
  description = "Name of the Lambda function to monitor (set once Lambda is deployed)"
  type        = string
  default     = "placeholder-lambda"
}
