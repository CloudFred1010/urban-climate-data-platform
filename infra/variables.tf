# ===============================
# Variables
# ===============================
variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "eu-west-2"
}

variable "redshift_username" {
  description = "Master username for Redshift"
  type        = string
  default     = "admin"
}

variable "redshift_password" {
  description = "Master password for Redshift (stored in Secrets Manager)"
  type        = string
  sensitive   = true
}

variable "redshift_node_type" {
  description = "Instance type for Redshift cluster nodes"
  type        = string
  default     = "ra3.large"
}

variable "redshift_nodes" {
  description = "Number of nodes in the Redshift cluster"
  type        = number
  default     = 2
}