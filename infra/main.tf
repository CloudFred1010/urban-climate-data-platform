########################################
# Provider
########################################
provider "aws" {
  region = var.aws_region
}

########################################
# Data Sources
########################################
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

########################################
# S3 Bucket – Raw Data Lake
########################################
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

########################################
# IAM Role for Redshift
########################################
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

########################################
# Secrets Manager – Redshift Admin Password
########################################
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

########################################
# Redshift Subnet Group & Cluster
########################################
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

########################################
# Redshift Audit Logging → S3
########################################
# Ensure bucket ownership is correct
resource "aws_s3_bucket_ownership_controls" "redshift_audit" {
  bucket = aws_s3_bucket.raw_data.id

  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

# Bucket policy to allow Redshift to log
resource "aws_s3_bucket_policy" "redshift_audit" {
  bucket = aws_s3_bucket.raw_data.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "RedshiftAuditLogging"
        Effect = "Allow"
        Principal = {
          Service = "redshift.amazonaws.com"
        }
        Action = [
          "s3:PutObject",
          "s3:GetBucketAcl",
          "s3:GetBucketLocation"
        ]
        Resource = [
          "${aws_s3_bucket.raw_data.arn}/audit/*",
          aws_s3_bucket.raw_data.arn
        ]
      }
    ]
  })
}

resource "aws_redshift_logging" "main" {
  cluster_identifier = aws_redshift_cluster.main.id
  bucket_name        = aws_s3_bucket.raw_data.bucket
  s3_key_prefix      = "audit/"
}

########################################
# Monitoring & Reliability
########################################
# SNS Topic for Alerts
resource "aws_sns_topic" "alerts" {
  name = "urban-climate-alerts"

  tags = {
    Project = "Urban Climate Data Platform"
    Purpose = "Monitoring Alerts"
  }
}

resource "aws_sns_topic_subscription" "email_alert" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# Redshift query failure alarm
resource "aws_cloudwatch_metric_alarm" "redshift_query_failures" {
  alarm_name          = "redshift-query-failures"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "QueriesFailed"
  namespace           = "AWS/Redshift"
  period              = var.cloudwatch_evaluation_period
  statistic           = "Sum"
  threshold           = var.redshift_query_failure_threshold
  alarm_actions       = [aws_sns_topic.alerts.arn]

  tags = {
    Project = "Urban Climate Data Platform"
    Purpose = "Monitoring"
  }
}

# Redshift high CPU alarm
resource "aws_cloudwatch_metric_alarm" "redshift_high_cpu" {
  alarm_name          = "redshift-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/Redshift"
  period              = var.cloudwatch_evaluation_period
  statistic           = "Average"
  threshold           = var.redshift_high_cpu_threshold
  alarm_description   = "Alarm if Redshift cluster CPU exceeds threshold"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  tags = {
    Project = "Urban Climate Data Platform"
    Purpose = "Performance Monitoring"
  }
}

# S3 4xx error alarm
resource "aws_cloudwatch_metric_alarm" "s3_4xx_errors" {
  alarm_name          = "s3-4xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "4xxErrors"
  namespace           = "AWS/S3"
  period              = var.cloudwatch_evaluation_period
  statistic           = "Sum"
  threshold           = var.s3_4xx_error_threshold
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    BucketName  = aws_s3_bucket.raw_data.bucket
    StorageType = "AllStorageTypes"
  }

  tags = {
    Project = "Urban Climate Data Platform"
    Purpose = "S3 Monitoring"
  }
}

# S3 5xx error alarm
resource "aws_cloudwatch_metric_alarm" "s3_5xx_errors" {
  alarm_name          = "s3-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "5xxErrors"
  namespace           = "AWS/S3"
  period              = var.cloudwatch_evaluation_period
  statistic           = "Sum"
  threshold           = var.s3_5xx_error_threshold
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    BucketName  = aws_s3_bucket.raw_data.bucket
    StorageType = "AllStorageTypes"
  }

  tags = {
    Project = "Urban Climate Data Platform"
    Purpose = "S3 Monitoring"
  }
}

# EMR step failure alarm (placeholder until EMR exists)
resource "aws_cloudwatch_metric_alarm" "emr_step_failures" {
  alarm_name          = "emr-step-failures"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "FailedSteps"
  namespace           = "AWS/ElasticMapReduce"
  period              = var.cloudwatch_evaluation_period
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Alarm if any EMR step fails"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    JobFlowId = "j-XXXXXXXXXXXXX" # placeholder
  }

  tags = {
    Project = "Urban Climate Data Platform"
    Purpose = "EMR Monitoring"
  }
}

# Lambda error alarm (placeholder until Lambda exists)
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "lambda-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = var.cloudwatch_evaluation_period
  statistic           = "Sum"
  threshold           = 1
  alarm_description   = "Alarm if Lambda reports errors"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    FunctionName = var.lambda_function_name
  }

  tags = {
    Project = "Urban Climate Data Platform"
    Purpose = "Lambda Monitoring"
  }
}

resource "aws_s3_bucket" "curated_data" {
  bucket        = "urban-climate-curated-${data.aws_caller_identity.current.account_id}"
  force_destroy = true
  tags = {
    Project = "Urban Climate Data Platform"
    Purpose = "Curated Data Lake"
  }
}
