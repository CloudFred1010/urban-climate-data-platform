provider "aws" {
  region = var.aws_region
}

# S3 bucket for raw data
resource "aws_s3_bucket" "raw_data" {
  bucket        = "urban-climate-raw"
  force_destroy = true

  tags = {
    Project = "Urban Climate Data Platform"
    Purpose = "Raw Data Lake"
  }
}

# Fetch the default VPC
data "aws_vpc" "default" {
  default = true
}

# Fetch all subnets from the default VPC
data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# Redshift Subnet Group (using default subnets)
resource "aws_redshift_subnet_group" "main" {
  name        = "urban-climate-redshift-subnet"
  description = "Subnet group for Redshift cluster"
  subnet_ids  = data.aws_subnets.default.ids
}

# IAM role for Redshift to access S3
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

# Attach AmazonS3ReadOnlyAccess policy to IAM role
resource "aws_iam_role_policy_attachment" "redshift_s3_access" {
  role       = aws_iam_role.redshift_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
}

# Redshift Cluster
resource "aws_redshift_cluster" "main" {
  cluster_identifier         = "urban-climate-cluster"
  node_type                  = var.redshift_node_type
  number_of_nodes            = var.redshift_nodes
  master_username            = var.redshift_username
  master_password            = var.redshift_password
  database_name              = "urbanclimate"             # ✅ Added explicit DB name
  cluster_type               = "multi-node"
  cluster_subnet_group_name  = aws_redshift_subnet_group.main.name
  skip_final_snapshot        = true
  publicly_accessible        = false
  iam_roles                  = [aws_iam_role.redshift_role.arn] # ✅ Ensures IAM role is applied

  tags = {
    Project = "Urban Climate Data Platform"
    Purpose = "Analytics Warehouse"
  }
}
