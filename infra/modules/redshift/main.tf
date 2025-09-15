########################################
# IAM Role for Redshift S3 Access
########################################

resource "aws_iam_role" "redshift_role" {
  name = "${var.cluster_identifier}-redshift-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "redshift.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_policy" "redshift_s3_policy" {
  name        = "${var.cluster_identifier}-redshift-s3-policy"
  description = "Allow Redshift read access to S3"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["s3:GetObject", "s3:ListBucket"]
        Resource = [
          var.s3_bucket_arn,
          "${var.s3_bucket_arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "redshift_s3_access" {
  role       = aws_iam_role.redshift_role.name
  policy_arn = aws_iam_policy.redshift_s3_policy.arn
}

########################################
# Subnet Group
########################################

resource "aws_redshift_subnet_group" "main" {
  name        = "${var.cluster_identifier}-subnet"
  description = "Subnet group for Redshift cluster"
  subnet_ids  = var.subnet_ids
}

########################################
# Redshift Cluster
########################################

resource "aws_redshift_cluster" "main" {
  cluster_identifier = var.cluster_identifier
  node_type          = var.node_type
  number_of_nodes    = var.number_of_nodes

  # Credentials (coming from Secrets Manager at env-level)
  master_username = var.redshift_username
  master_password = var.redshift_password

  database_name             = "urbanclimate"
  cluster_type              = "multi-node"
  cluster_subnet_group_name = aws_redshift_subnet_group.main.name
  skip_final_snapshot       = true

  # 🔹 Now configurable via env-level variables
  publicly_accessible    = var.publicly_accessible
  vpc_security_group_ids = var.vpc_security_group_ids

  iam_roles = [aws_iam_role.redshift_role.arn]

  tags = {
    Project = "Urban Climate Data Platform"
    Purpose = "Analytics Warehouse"
  }

  # Prevent accidental destructive changes
  lifecycle {
    ignore_changes = [
      database_name,
      master_password # Redshift ignores updates — rotate via Secrets Manager
    ]
  }
}

########################################
# Logging
########################################

resource "aws_redshift_logging" "main" {
  cluster_identifier = aws_redshift_cluster.main.id
  bucket_name        = var.s3_bucket_name
  s3_key_prefix      = "audit/"
}

########################################
# Outputs (for env-level consumption)
########################################

output "redshift_endpoint" {
  value       = aws_redshift_cluster.main.endpoint
  description = "JDBC endpoint for the Redshift cluster"
}

output "redshift_database" {
  value       = aws_redshift_cluster.main.database_name
  description = "Default database name in the cluster"
}

output "redshift_cluster_id" {
  value       = aws_redshift_cluster.main.id
  description = "Cluster identifier"
}

output "redshift_cluster_arn" {
  value       = aws_redshift_cluster.main.arn
  description = "Cluster ARN"
}

output "redshift_role_arn" {
  value       = aws_iam_role.redshift_role.arn
  description = "IAM role ARN used by Redshift for S3 access"
}
