import boto3
import time
import pandas as pd
import os

# ============================================================
# Config
# ============================================================
DATABASE = "urban_climate_db"
OUTPUT_BUCKET = "urban-climate-raw-235562991700"
OUTPUT_PREFIX = "query-results/"
OUTPUT_LOCATION = f"s3://{OUTPUT_BUCKET}/{OUTPUT_PREFIX}"

QUERY = """
SELECT region_code, year, population, uvi
FROM urban_vulnerability
LIMIT 10;
"""

LOCAL_RESULTS_FILE = "./athena_results.csv"

# ============================================================
# Athena Client
# ============================================================
athena = boto3.client(
    "athena", region_name=os.getenv("AWS_DEFAULT_REGION", "eu-west-2")
)
s3 = boto3.client("s3")

# ============================================================
# Run Athena Query
# ============================================================
print("Starting Athena query...")
response = athena.start_query_execution(
    QueryString=QUERY,
    QueryExecutionContext={"Database": DATABASE},
    ResultConfiguration={"OutputLocation": OUTPUT_LOCATION},
)

query_execution_id = response["QueryExecutionId"]
print(f"QueryExecutionId: {query_execution_id}")

# ============================================================
# Wait for Query to Finish
# ============================================================
state = "RUNNING"
while state in ["RUNNING", "QUEUED"]:
    response = athena.get_query_execution(QueryExecutionId=query_execution_id)
    state = response["QueryExecution"]["Status"]["State"]
    if state == "FAILED":
        reason = response["QueryExecution"]["Status"]["StateChangeReason"]
        raise Exception(f"Query FAILED: {reason}")
    elif state == "CANCELLED":
        raise Exception("Query was CANCELLED")
    print("Waiting for query to finish...")
    time.sleep(3)

print("Query succeeded!")

# ============================================================
# Download Result CSV from S3
# ============================================================
result_key = f"{OUTPUT_PREFIX}{query_execution_id}.csv"
print(
    f"Downloading results from s3://{OUTPUT_BUCKET}/{result_key} -> {LOCAL_RESULTS_FILE}"
)

s3.download_file(OUTPUT_BUCKET, result_key, LOCAL_RESULTS_FILE)

# ============================================================
# Load with Pandas
# ============================================================
df = pd.read_csv(LOCAL_RESULTS_FILE)
print("\n===== Athena Query Results =====")
print(df.head(10))
