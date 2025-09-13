# Monitoring & Reliability

## Alerts
- All alerts routed via SNS topic: `urban-climate-alerts`
- Current subscription: `${var.alert_email}`

## Redshift
- CloudWatch alarm: failed queries
- CloudWatch alarm: CPU Utilization > 80%
- Logs written to S3 at `s3://urban-climate-raw-<account-id>/redshift-logs/`

## EMR
- Alarms: failed steps, terminated with errors

## S3
- Alarms: 4xx/5xx errors

## Lambda (future)
- Errors, throttles, duration alarms
