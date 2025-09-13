import os
import json
import boto3
import pandas as pd
import osmium
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, LongType, DoubleType, StringType

# ---------- Spark Setup ----------
spark = (
    SparkSession.builder.appName("UrbanClimateETL")
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    .config(
        "spark.hadoop.fs.s3a.aws.credentials.provider",
        "com.amazonaws.auth.DefaultAWSCredentialsProviderChain",
    )
    .config(
        "spark.jars.packages",
        "org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262",
    )
    .config("spark.driver.memory", "4g")
    .config("spark.executor.memory", "4g")
    .getOrCreate()
)

# ---------- Config ----------
RAW_BUCKET = os.getenv("RAW_BUCKET", "urban-climate-raw-235562991700")

# Weather
RAW_PREFIX_WEATHER = "raw/weather/"
PROCESSED_PREFIX_WEATHER = "processed/weather/"

# Geospatial
RAW_PREFIX_GEO = "raw/geospatial/"
PROCESSED_PREFIX_GEO = "processed/geospatial/"

s3_client = boto3.client("s3")


# ---------- Weather ETL ----------
def list_weather_files():
    response = s3_client.list_objects_v2(Bucket=RAW_BUCKET, Prefix=RAW_PREFIX_WEATHER)
    if "Contents" not in response:
        return []
    return [obj["Key"] for obj in response["Contents"] if obj["Key"].endswith(".json")]


def run_weather_etl():
    files = list_weather_files()
    if not files:
        print("No raw weather files found in S3")
        return

    for key in files:
        s3_path = f"s3a://{RAW_BUCKET}/{key}"
        print(f"Processing {s3_path}")

        df = spark.read.json(s3_path)
        pdf = df.toPandas().dropna(how="all")

        if "dt" in pdf.columns:
            pdf["dt"] = pd.to_datetime(pdf["dt"], unit="s", errors="coerce")

        clean_df = spark.createDataFrame(pdf)
        out_path = f"s3a://{RAW_BUCKET}/{PROCESSED_PREFIX_WEATHER}"
        clean_df.write.mode("append").parquet(out_path)
        print(f"Written cleaned weather data to {out_path}")


# ---------- Geospatial ETL (PyOsmium with chunking) ----------
class OSMHandler(osmium.SimpleHandler):
    def __init__(self, bbox=None, flush_size=500000):
        super().__init__()
        self.nodes = []
        self.bbox = bbox
        self.flush_size = flush_size
        self.batch_counter = 0

    def node(self, n):
        if n.location.valid():
            if self.bbox:  # Optional filter
                if not (
                    self.bbox[0] <= n.location.lon <= self.bbox[2]
                    and self.bbox[1] <= n.location.lat <= self.bbox[3]
                ):
                    return
            self.nodes.append(
                {
                    "id": n.id,
                    "lat": n.location.lat,
                    "lon": n.location.lon,
                    "tags": json.dumps(dict(n.tags)),
                }
            )

            # Flush in chunks
            if len(self.nodes) >= self.flush_size:
                self.flush_to_s3()

    def flush_to_s3(self):
        if not self.nodes:
            return
        pdf = pd.DataFrame(self.nodes)
        schema = StructType(
            [
                StructField("id", LongType(), False),
                StructField("lat", DoubleType(), True),
                StructField("lon", DoubleType(), True),
                StructField("tags", StringType(), True),
            ]
        )
        spark_df = spark.createDataFrame(pdf, schema=schema)
        out_path = f"s3a://{RAW_BUCKET}/{PROCESSED_PREFIX_GEO}"
        spark_df.write.mode("append").option("mergeSchema", "true").parquet(out_path)
        self.batch_counter += 1
        print(
            f"Flushed batch {self.batch_counter} ({len(self.nodes)} nodes) to {out_path}"
        )
        self.nodes = []  # reset buffer


def list_geo_files():
    response = s3_client.list_objects_v2(Bucket=RAW_BUCKET, Prefix=RAW_PREFIX_GEO)
    if "Contents" not in response:
        return []
    return [
        obj["Key"] for obj in response["Contents"] if obj["Key"].endswith(".osm.pbf")
    ]


def run_geospatial_etl():
    files = list_geo_files()
    if not files:
        print("No raw geospatial files found in S3")
        return

    for key in files:
        local_file = f"/tmp/{os.path.basename(key)}"
        print(f"Downloading {key} → {local_file}")
        s3_client.download_file(RAW_BUCKET, key, local_file)

        if os.path.getsize(local_file) < 50000:
            print(f"Skipping invalid/empty PBF: {key}")
            os.remove(local_file)
            continue

        # FIX: process ALL nodes (no bbox restriction)
        handler = OSMHandler(bbox=None)

        try:
            handler.apply_file(local_file)
            handler.flush_to_s3()  # flush remaining nodes
        except RuntimeError as e:
            print(f"Error parsing {key}: {e}")

        os.remove(local_file)
        print(f"Finished processing {key}")


# ---------- Main ----------
if __name__ == "__main__":
    run_weather_etl()
    run_geospatial_etl()
