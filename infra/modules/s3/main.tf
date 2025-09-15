########################################
# S3 Buckets for Raw & Curated Data
########################################

resource "aws_s3_bucket" "raw_data" {
  bucket        = var.bucket_name_raw
  force_destroy = true

  tags = {
    Project = "Urban Climate Data Platform"
    Purpose = "Raw Data Lake"
  }
}

resource "aws_s3_bucket" "curated_data" {
  bucket        = var.bucket_name_curated
  force_destroy = true

  tags = {
    Project = "Urban Climate Data Platform"
    Purpose = "Curated Data Lake"
  }
}

########################################
# Raw Data Prefixes
########################################

resource "aws_s3_object" "prefixes" {
  for_each = toset(["raw/weather/", "raw/demographics/", "raw/geospatial/"])
  bucket   = aws_s3_bucket.raw_data.id
  key      = each.value
  content  = "" # marker object
}

########################################
# Ownership & Policy for Redshift Audit Logs
########################################

resource "aws_s3_bucket_ownership_controls" "redshift_audit" {
  bucket = aws_s3_bucket.raw_data.id

  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

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
