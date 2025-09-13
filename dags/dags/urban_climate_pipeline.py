from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.utils.email import send_email
from airflow.models import Variable
import requests


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

    # Email
    send_email(
        to=["wilfr@example.com"],
        subject=f"[Airflow] Task Failed: {dag_id}.{task_id}",
        html_content=message,
    )

    # Slack (if webhook available in Variables)
    slack_webhook = Variable.get("slack_webhook", default_var=None)
    if slack_webhook:
        try:
            requests.post(slack_webhook, json={"text": message})
        except Exception:
            pass


# -------------------------------------------------------------------------
# Success notification
# -------------------------------------------------------------------------
def notify_success(**context):
    message = "Urban Climate ETL pipeline completed successfully."
    slack_webhook = Variable.get("slack_webhook", default_var=None)
    if slack_webhook:
        requests.post(slack_webhook, json={"text": message})
    send_email(
        to=["wilfr@example.com"],
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
    "email": ["wilfr@example.com"],
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "on_failure_callback": task_fail_alert,
}

# -------------------------------------------------------------------------
# Airflow Variables
# -------------------------------------------------------------------------
REDSHIFT_CLUSTER = Variable.get("redshift_cluster")
REDSHIFT_DB = Variable.get("redshift_db")
REDSHIFT_USER = Variable.get("redshift_user")
REDSHIFT_ROLE = Variable.get("redshift_role")  # IAM role with S3 read
GLUE_CRAWLER = Variable.get("glue_crawler")
CURATED_S3 = Variable.get(
    "curated_s3"
)  # e.g. s3://urban-climate-curated-235562991700/curated/uvi/

# -------------------------------------------------------------------------
# DAG
# -------------------------------------------------------------------------
with DAG(
    dag_id="urban_climate_pipeline",
    default_args=default_args,
    description="ETL → Redshift Load → Quality Checks → Notifications",
    schedule_interval="@daily",
    start_date=datetime(2025, 9, 12),
    catchup=False,
    tags=["urban", "climate", "etl"],
) as dag:

    # 1. Run ETL (Spark script)
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

    # 5. Notify success (Slack + Email)
    notify = PythonOperator(
        task_id="notify",
        python_callable=notify_success,
        provide_context=True,
    )

    # DAG flow
    run_etl >> refresh_partitions >> load_redshift >> quality_check >> notify
