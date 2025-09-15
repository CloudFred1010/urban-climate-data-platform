########################################
# Redshift Cluster Variables
########################################

variable "cluster_identifier" {
  description = "Identifier for the Redshift cluster"
  type        = string
}

variable "redshift_username" {
  description = "Master username for the Redshift cluster"
  type        = string
}

variable "redshift_password" {
  description = "Master password for the Redshift cluster (store in Secrets Manager in real environments)"
  type        = string
  sensitive   = true
}

variable "node_type" {
  description = "Redshift node type (e.g., ra3.large, dc2.large)"
  type        = string
}

variable "number_of_nodes" {
  description = "Number of Redshift nodes in the cluster"
  type        = number
}

variable "subnet_ids" {
  description = "List of subnet IDs to use for the Redshift subnet group"
  type        = list(string)
}

variable "s3_bucket_name" {
  description = "S3 bucket name for audit logging"
  type        = string
}

variable "s3_bucket_arn" {
  description = "ARN of the S3 bucket for Redshift S3 access"
  type        = string
}

########################################
# Networking & Access
########################################

variable "publicly_accessible" {
  description = "Whether the Redshift cluster should be publicly accessible (true for dev, false for prod)"
  type        = bool
  default     = false
}

variable "vpc_security_group_ids" {
  description = "List of VPC Security Group IDs to associate with Redshift"
  type        = list(string)
  default     = []
}
