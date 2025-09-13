# Phase 6 – Orchestration & Monitoring

## Overview
Phase 6 focuses on production-grade orchestration of ETL workflows, validation of cloud infrastructure, and implementation of monitoring and alerting. The outcome is a reliable and observable pipeline that can ingest, transform, validate, and load multimodal datasets into Redshift with automated quality checks and failure handling.

---

## Completed in Phase 6

### ETL Script
- `run_etl.py` fixed and running end-to-end:
  - Reads from S3 raw/processed
  - Joins datasets
  - Computes UVI
  - Writes parquet to curated S3 bucket
- Geo dataset fallback logic corrected (`region_code`, `year`, `infra_exposure`)
- Flood dataset handled safely (skip or fallback to 0)
- `DEV_MODE` tested successfully

### Infrastructure Validation
- `terraform validate` passed successfully
- Provisioned and confirmed: Redshift, S3 buckets, IAM roles, CloudWatch alarms, Secrets
- Curated S3 bucket creation attempted → already exists and owned (confirmed in Terraform state)

### Monitoring Setup
- CloudWatch alarms configured for:
  - S3 4xx/5xx errors
  - Redshift CPU utilisation and query failures
  - EMR step failures
  - Lambda errors
- SNS topic + email subscription wired and verified (alerts flowing to email)

---

## Still Pending in Phase 6

### Airflow DAG Orchestration
- Hook `run_etl.py` into Airflow DAG
- Define DAG steps:
  1. Extract
  2. Transform (PySpark on EMR)
  3. Load (Redshift COPY)
  4. Validate
  5. Notify

### Redshift Load Step
- Add COPY from curated parquet into `analytics.uvi`
- Confirm row counts and partition coverage in Redshift

### Data Quality Validation
- Enforce checks:
  - Non-null `region_code`
  - Non-null `year`
  - Non-null `uvi`
- Build checks into `validate_curated.py` and DAG task

### Alerting Integration
- Current: SNS → Email
- Pending: SNS → Slack channel for devops/data team visibility

### Terraform Refactor
- Split infra into reusable modules:
  - S3
  - Redshift
  - EMR
  - Alerts
- Support per-environment deployments (dev, staging, prod)

### Documentation
- Add `/docs/phase6-orchestration.md` with:
  - DAG diagram
  - Monitoring & alerts map
  - Infra module usage
  - Runbook for failures (Redshift COPY fails, EMR step fail, S3 permission issues)
  - Operational playbooks & lessons learned

---

## DAG Diagram
Extract → Transform (Spark/EMR) → Load (Redshift COPY) → Validate → Notify

---

## Monitoring & Alerts Map
CloudWatch alarms currently configured:
- S3: 4xx/5xx error spikes
- Redshift: CPU utilisation and query failures
- EMR: Step execution failures
- Lambda: Error count
- Airflow: Task retries/failures logged

Alerts currently flow to SNS → Email. Pending: SNS → Slack for real-time visibility.

---

## Infrastructure Module Usage
Infrastructure provisioned via Terraform. Planned refactor into reusable modules:
- s3/ → Buckets for raw, processed, curated
- redshift/ → Cluster, IAM roles, schema setup
- emr/ → Cluster configuration for Spark jobs
- alerts/ → CloudWatch + SNS alarms

Each module will support dev, staging, and prod environments.

---

## Runbook for Failure Cases

### Redshift COPY Fails
**Symptoms**  
- COPY command fails with `AccessDenied` or `S3ServiceException`

**Recovery**  
1. Confirm IAM role attached to Redshift has `s3:GetObject` and `s3:ListBucket`  
2. Test access with:  
   `aws s3 ls s3://curated-bucket/uvi/`  
3. Re-run COPY:  


COPY analytics.uvi FROM 's3://curated-bucket/uvi/'
IAM_ROLE 'arn:aws:iam::<account-id>:role/RedshiftCopyRole'
FORMAT AS PARQUET


### EMR Step Fail
**Symptoms**  
`Caused by: org.apache.spark.SparkException: Job aborted due to stage failure`

**Recovery**  
1. Review EMR console → Cluster → Steps  
2. If transient (network or S3 read timeout), retry with:  
`aws emr add-steps --cluster-id <cluster> --steps file://etl-step.json`  
3. If persistent, escalate to platform team (review Spark job logic, memory allocation)

### S3 Permission Issues
**Symptoms**  
- Airflow or EMR unable to read/write S3 objects

**Recovery**  
1. Validate IAM policy & bucket policy  
2. Test access with:  
`aws s3 ls s3://curated-bucket/uvi/`  
3. Ensure IAM role includes:  
- `s3:GetObject`  
- `s3:ListBucket`  
- `s3:PutObject`

---

## Operational Playbooks & Lessons Learned

### Known Gotchas
- Airflow DAGs must be unpaused after deployment
- Redshift COPY requires explicit S3 read role
- S3 objects may take seconds to appear; retries required
- EMR bootstrap time can delay first job by 10–15 minutes

### Sample Log Outputs
Airflow Task Retry:  
`[2025-09-13 21:15:23] Task failed with Exit Code 1`  
`[2025-09-13 21:15:23] Retrying in 300 seconds`  

Redshift COPY Failure:  
`ERROR: S3ServiceException:AccessDenied`  
`DETAIL: Cannot read from S3 location s3://curated-bucket/uvi/`  

EMR Step Failure:  
`Caused by: org.apache.spark.SparkException: Job aborted due to stage failure`

### Recovery Procedures
**Airflow**  
- Go to Airflow UI → DAGs → Select failing task  
- Inspect logs for cause  
- Clear and re-run task  

**EMR**  
- Review step failure in EMR console  
- Retry via CLI:  
`aws emr add-steps --cluster-id <cluster> --steps file://etl-step.json`  

**Redshift**  
- Verify IAM role permissions  
- Retry COPY manually with explicit IAM role  

**S3**  
- Check IAM role and bucket policy  
- Test with `aws s3 ls` or `aws s3 cp`  

### Escalation & Decision Tree
On-Call Engineer Can Resolve:
- Airflow task retries
- Redshift COPY with missing partitions
- EMR transient failures (retry once)

Escalate to Data/Platform Team:
- IAM permission errors persisting after retry
- Redshift cluster capacity/resource exhaustion
- Consistent EMR Spark job logic errors

---

## Next Steps
- Finalise Airflow DAG integration with `run_etl.py`
- Add Redshift load validation into DAG
- Complete SNS → Slack alert integration
- Refactor Terraform into modules with per-environment deployments
- Expand runbook with RTO/RPO expectations and escalation timelines
