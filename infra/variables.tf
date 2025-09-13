# ===============================
# Variables
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
