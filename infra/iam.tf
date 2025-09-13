resource "aws_iam_user_policy" "urban_climate_etl" {
  name = "UrbanClimateETLPolicy"
  user = "terraform-devops"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "glue:StartCrawler",
          "glue:GetCrawler",
          "glue:GetCrawlerMetrics"
        ]
        Resource = "arn:aws:glue:${var.aws_region}:${data.aws_caller_identity.current.account_id}:crawler/uvi-curated-crawler"
      },
      {
        Effect = "Allow"
        Action = [
          "redshift-data:ExecuteStatement",
          "redshift-data:GetStatementResult",
          "redshift-data:DescribeStatement"
        ]
        Resource = "*"
      }
    ]
  })
}
