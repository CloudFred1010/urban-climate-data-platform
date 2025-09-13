provider "aws" {
  region = var.aws_region
}

# ===============================
# Data Sources
# ===============================
data "aws_caller_identity" "current" {}

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# ===============================
# S3 Bucket (Raw Data Lake)
# ===============================
resource "aws_s3_bucket" "raw_data" {
  bucket        = "urban-climate-raw-${data.aws_caller_identity.current.account_id}"
  force_destroy = true

  tags = {
    Project = "Urban Climate Data Platform"
    Purpose = "Raw Data Lake"
  }
}

resource "aws_s3_object" "prefixes" {
  for_each = toset(["raw/weather/", "raw/demographics/", "raw/geospatial/"])
  bucket   = aws_s3_bucket.raw_data.id
  key      = each.value
  content  = "" # marker object
}

# ===============================
# IAM for Redshift
# ===============================
resource "aws_iam_role" "redshift_role" {
  name = "urban-climate-redshift-role"

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
  name        = "urban-climate-redshift-s3-policy"
  description = "Allow Redshift read access to raw data bucket"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["s3:GetObject", "s3:ListBucket"]
        Resource = [
          aws_s3_bucket.raw_data.arn,
          "${aws_s3_bucket.raw_data.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "redshift_s3_access" {
  role       = aws_iam_role.redshift_role.name
  policy_arn = aws_iam_policy.redshift_s3_policy.arn
}

# ===============================
# Secrets Manager – Redshift Admin Password
# ===============================
resource "aws_secretsmanager_secret" "redshift_password" {
  name = "redshift-admin-password"

  tags = {
    Project = "Urban Climate Data Platform"
    Purpose = "Store Redshift Admin Password"
  }
}

resource "aws_secretsmanager_secret_version" "redshift_password_value" {
  secret_id     = aws_secretsmanager_secret.redshift_password.id
  secret_string = var.redshift_password
}

# ===============================
# Redshift Subnet Group & Cluster
# ===============================
resource "aws_redshift_subnet_group" "main" {
  name        = "urban-climate-redshift-subnet"
  description = "Subnet group for Redshift cluster"
  subnet_ids  = data.aws_subnets.default.ids
}

resource "aws_redshift_cluster" "main" {
  cluster_identifier        = "urban-climate-cluster"
  node_type                 = var.redshift_node_type
  number_of_nodes           = var.redshift_nodes
  master_username           = var.redshift_username
  master_password           = var.redshift_password
  database_name             = "urbanclimate"
  cluster_type              = "multi-node"
  cluster_subnet_group_name = aws_redshift_subnet_group.main.name
  skip_final_snapshot       = true
  publicly_accessible       = false
  iam_roles                 = [aws_iam_role.redshift_role.arn]

  tags = {
    Project = "Urban Climate Data Platform"
    Purpose = "Analytics Warehouse"
  }

  lifecycle {
    ignore_changes = [
      database_name,
      master_password
    ]
  }
}
