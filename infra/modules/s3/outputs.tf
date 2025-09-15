output "raw_bucket_name" {
  description = "Name of the raw data S3 bucket"
  value       = aws_s3_bucket.raw_data.bucket
}

output "curated_bucket_name" {
  description = "Name of the curated data S3 bucket"
  value       = aws_s3_bucket.curated_data.bucket
}

output "raw_prefixes" {
  description = "Standard prefixes for raw data organisation in S3"
  value = {
    weather      = "${aws_s3_bucket.raw_data.bucket}/raw/weather/"
    demographics = "${aws_s3_bucket.raw_data.bucket}/raw/demographics/"
    geospatial   = "${aws_s3_bucket.raw_data.bucket}/raw/geospatial/"
  }
}
