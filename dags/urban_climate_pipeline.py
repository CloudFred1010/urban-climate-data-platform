from datetime import datetime, timedelta
import requests
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.utils.email import send_email
from airflow.models import Variable


# -------------------------------------------------------------------------
# Failure alert callback (email + optional Slack)
# -------------------------------------------------------------------------
def task_fail_alert(context):
    dag_id = context.get("dag").dag_id
    task_id = context.get("task_instance").task_id
    exec_date = context.get("execution_date")
    log_url = context.get("task_instance").log_url

    message = f"""
    Task Failed
    DAG: {dag_id}
    Task: {task_id}
    Execution Time: {exec_date}
    Logs: {log_url}
    """

    # Email alert
    send_email(
        to=[Variable.get("alert_email", default_var="wilfr@example.com")],
        subject=f"[Airflow] Task Failed: {dag_id}.{task_id}",
        html_content=message,
    )

    # Slack alert (if webhook configured)
    slack_webhook = Variable.get("slack_webhook", default_var=None)
    if slack_webhook:
        try:
            requests.post(slack_webhook, json={"text": message})
        except Exception as e:
            print(f"Slack notification failed: {e}")


# -------------------------------------------------------------------------
# Success notification
# -------------------------------------------------------------------------
def notify_success(**context):
    message = "Urban Climate ETL pipeline completed successfully."
    slack_webhook = Variable.get("slack_webhook", default_var=None)
    if slack_webhook:
        try:
            requests.post(slack_webhook, json={"text": message})
        except Exception as e:
            print(f"Slack notification failed: {e}")

    send_email(
        to=[Variable.get("alert_email", default_var="wilfr@example.com")],
        subject="[Airflow] ETL Success",
        html_content=message,
    )


# -------------------------------------------------------------------------
# Default args
# -------------------------------------------------------------------------
default_args = {
    "owner": "wilfr",
    "depends_on_past": False,
    "email_on_failure": True,
    "email_on_retry": False,
    "email": [Variable.get("alert_email", default_var="wilfr@example.com")],
    "retries": 2,
    "retry_delay": timedelta(minutes=10),
    "on_failure_callback": task_fail_alert,
}


# -------------------------------------------------------------------------
# Airflow Variables (hooked to Terraform outputs)
# -------------------------------------------------------------------------
REDSHIFT_CLUSTER = Variable.get("redshift_cluster", default_var="urban-climate-cluster")
REDSHIFT_DB = Variable.get("redshift_db", default_var="urbanclimate")
REDSHIFT_USER = Variable.get("redshift_user", default_var="admin")
REDSHIFT_ROLE = Variable.get("redshift_role")
GLUE_CRAWLER = Variable.get("glue_crawler", default_var="urban-climate-crawler")
CURATED_S3 = Variable.get(
    "curated_s3",
    default_var="s3://urban-climate-curated-123456789012/curated/uvi/",
)


# -------------------------------------------------------------------------
# DAG Definition
# -------------------------------------------------------------------------
with DAG(
    dag_id="urban_climate_pipeline",
    default_args=default_args,
    description="ETL → Redshift Load → Quality Checks → Notifications",
    schedule_interval="@daily",
    start_date=datetime(2025, 9, 12),
    catchup=False,
    max_active_runs=1,
    tags=["urban", "climate", "etl", "redshift", "s3"],
) as dag:

    # 1. Run ETL (Spark job on EMR or local test script)
    run_etl = BashOperator(
        task_id="run_etl",
        bash_command="python3 /home/wilfr/Project-Amini/urban-climate-data-platform/etl/run_etl.py",
    )

    # 2. Refresh Glue partitions
    refresh_partitions = BashOperator(
        task_id="refresh_partitions",
        bash_command=f"aws glue start-crawler --name {GLUE_CRAWLER}",
    )

    # 3. Load curated data into Redshift staging
    load_redshift = BashOperator(
        task_id="load_redshift",
        bash_command=(
            f"aws redshift-data execute-statement "
            f"--cluster-identifier {REDSHIFT_CLUSTER} "
            f"--database {REDSHIFT_DB} "
            f"--db-user {REDSHIFT_USER} "
            f'--sql "COPY staging.uvi_curated '
            f"FROM '{CURATED_S3}' "
            f"IAM_ROLE '{REDSHIFT_ROLE}' "
            f'FORMAT AS PARQUET;" '
            "> /tmp/redshift_load.log"
        ),
    )

    # 4. Run validation queries
    quality_check = BashOperator(
        task_id="quality_check",
        bash_command=(
            f"aws redshift-data execute-statement "
            f"--cluster-identifier {REDSHIFT_CLUSTER} "
            f"--database {REDSHIFT_DB} "
            f"--db-user {REDSHIFT_USER} "
            '--sql "SELECT COUNT(*) AS row_count, MIN(uvi), MAX(uvi) FROM staging.uvi_curated;" '
            "> /tmp/redshift_quality.log"
        ),
    )

    # 5. Notify success
    notify = PythonOperator(
        task_id="notify",
        python_callable=notify_success,
    )

    # DAG Flow
    run_etl >> refresh_partitions >> load_redshift >> quality_check >> notify
