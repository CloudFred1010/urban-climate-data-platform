########################################
# Providers
########################################
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    http = {
      source  = "hashicorp/http"
      version = "~> 3.5"
    }
  }
}

provider "aws" {
  region = "eu-west-2"
}

########################################
# S3 Buckets (Raw + Curated)
########################################
module "s3" {
  source              = "../../modules/s3"
  bucket_name_raw     = "urban-climate-raw-dev"
  bucket_name_curated = "urban-climate-curated-dev"
}

########################################
# VPC & Subnets
########################################
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

########################################
# Security Group for Redshift (Dev only)
########################################
data "http" "my_ip" {
  url = "http://checkip.amazonaws.com/"
}

resource "aws_security_group" "redshift_sg" {
  name        = "redshift-dev-sg"
  description = "Allow psql access to Redshift (dev only)"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    from_port   = 5439
    to_port     = 5439
    protocol    = "tcp"
    cidr_blocks = [format("%s/32", chomp(data.http.my_ip.response_body))]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Project = "Urban Climate Data Platform"
    Purpose = "Dev Redshift Access"
  }
}

########################################
# Secrets Manager for Redshift
########################################
resource "aws_secretsmanager_secret" "redshift_secret" {
  name        = "redshift-dev-password"
  description = "Master credentials for Redshift dev cluster"
}

resource "aws_secretsmanager_secret_version" "redshift_secret_value" {
  secret_id = aws_secretsmanager_secret.redshift_secret.id
  secret_string = jsonencode({
    username = "admin"
    password = "YourStrongPassword123!" # rotate manually or with Secrets Manager rotation
  })
}

# Always fetch the latest secret for use
data "aws_secretsmanager_secret" "redshift_secret_data" {
  arn = aws_secretsmanager_secret.redshift_secret.arn
}

data "aws_secretsmanager_secret_version" "redshift_secret_version" {
  secret_id = data.aws_secretsmanager_secret.redshift_secret_data.id
}

locals {
  redshift_secret = jsondecode(data.aws_secretsmanager_secret_version.redshift_secret_version.secret_string)
}

########################################
# Redshift Cluster (Dev)
########################################
module "redshift" {
  source             = "../../modules/redshift"
  cluster_identifier = "urban-climate-dev"

  # Credentials pulled dynamically from Secrets Manager
  redshift_username = local.redshift_secret.username
  redshift_password = local.redshift_secret.password

  # Node config
  node_type       = "ra3.large"
  number_of_nodes = 2

  # Networking
  subnet_ids             = data.aws_subnets.default.ids
  publicly_accessible    = true
  vpc_security_group_ids = [aws_security_group.redshift_sg.id]

  # S3 integration (logging + access)
  s3_bucket_name = module.s3.raw_bucket_name
  s3_bucket_arn  = "arn:aws:s3:::${module.s3.raw_bucket_name}"
}
