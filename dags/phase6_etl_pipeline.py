from datetime import datetime, timedelta
import logging

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator

# --------------------
# Default DAG arguments
# --------------------
default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "email": ["alerts@yourdomain.com"],  # optional
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

# --------------------
# DAG definition
# --------------------
with DAG(
    dag_id="phase6_etl_pipeline",
    default_args=default_args,
    description="Phase 6 ETL Orchestration: Extract -> Transform -> Load -> Validate -> Notify",
    schedule="0 2 * * *",  # daily at 2 AM
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["phase6", "etl", "uvi"],
) as dag:

    # --------------------
    # Extract
    # --------------------
    extract_task = BashOperator(
        task_id="extract",
        bash_command=(
            "set -e; "
            "python3 /home/wilfr/Project-Amini/urban-climate-data-platform/etl/extract_data.py"
        ),
    )

    # --------------------
    # Transform
    # --------------------
    transform_task = BashOperator(
        task_id="transform",
        bash_command=(
            "set -e; "
            "python3 /home/wilfr/Project-Amini/urban-climate-data-platform/etl/run_etl.py"
        ),
    )

    # --------------------
    # Load into Redshift
    # --------------------
    load_task = SQLExecuteQueryOperator(
        task_id="load_redshift",
        conn_id="redshift_default",  # must point to admin user
        sql="""
            COPY analytics.uvi
            FROM '{{ var.value.s3_curated_path }}'
            IAM_ROLE '{{ var.value.redshift_role }}'
            FORMAT AS PARQUET;
        """,
        hook_params={"schema": "analytics"},
    )

    # --------------------
    # Validate
    # --------------------
    validate_task = BashOperator(
        task_id="validate",
        bash_command=(
            "set -e; "
            "python3 /home/wilfr/Project-Amini/urban-climate-data-platform/etl/validate_curated.py"
        ),
    )

    # --------------------
    # Notify
    # --------------------
    def notify():
        logging.info("✅ Phase 6 pipeline completed successfully.")

    notify_task = PythonOperator(
        task_id="notify",
        python_callable=notify,
    )

    # --------------------
    # Dependencies
    # --------------------
    extract_task >> transform_task >> load_task >> validate_task >> notify_task
