from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "wilfr",
    "depends_on_past": False,
    "email_on_failure": False,
    "email": ["wilfr@example.com"],
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="urban_climate_pipeline",
    default_args=default_args,
    description="ETL → Glue Crawler/MSCK REPAIR → Redshift Validation",
    schedule_interval="@daily",
    start_date=datetime(2025, 9, 12),
    catchup=False,
    tags=["urban", "climate", "etl"],
) as dag:

    run_etl = BashOperator(
        task_id="run_etl",
        bash_command="python3 /home/wilfr/Project-Amini/urban-climate-data-platform/etl/run_etl.py",
    )

    refresh_partitions = BashOperator(
        task_id="refresh_partitions",
        bash_command="aws glue start-crawler --name uvi-curated-crawler",
    )

    validate_redshift = BashOperator(
        task_id="validate_redshift",
        bash_command=(
            "aws redshift-data execute-statement "
            "--cluster-identifier urban-climate-cluster "
            "--database dev "
            "--db-user admin "
            '--sql "SELECT COUNT(*) FROM public.curated_urban_vulnerability;" '
            "> /tmp/redshift_validation.log"
        ),
    )

    run_etl >> refresh_partitions >> validate_redshift
