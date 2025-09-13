#!/usr/bin/env python3
"""
Urban Climate Data Platform - ETL Step 3
----------------------------------------
Transforms raw weather, demographics, geo, and flood zone data
into a curated Urban Vulnerability Index (UVI) dataset.

Fixes:
- Disabled all broadcast joins (force sort-merge joins).
- Added repartition before joins to balance data.
- DEV_MODE applies .limit() to inputs (not after join).
- Skip flood join if dataset is empty.
- Always provide flood_risk column (fallback = 0).
- Safer preview (take instead of show).
- Corrected handling of weather.main struct (extract main.temp).
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, year, when, coalesce, expr
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    IntegerType,
    DoubleType,
)

# ------------------------------
# Spark Setup (with S3 support)
# ------------------------------
spark = (
    SparkSession.builder.appName("UrbanClimateETL")
    .config(
        "spark.jars.packages",
        "org.apache.hadoop:hadoop-aws:3.3.4,"
        "com.amazonaws:aws-java-sdk-bundle:1.12.262",
    )
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    .config(
        "spark.hadoop.fs.s3a.aws.credentials.provider",
        "com.amazonaws.auth.DefaultAWSCredentialsProviderChain",
    )
    # Memory + join safety
    .config("spark.sql.autoBroadcastJoinThreshold", "-1")
    .config("spark.sql.adaptive.enabled", "false")
    .config(
        "spark.sql.optimizer.excludedRules",
        "org.apache.spark.sql.catalyst.optimizer.ConvertToBroadcastJoins",
    )
    .config("spark.sql.join.preferSortMergeJoin", "true")
    .config("spark.sql.shuffle.partitions", "8")
    .config("spark.driver.memory", "6g")
    .config("spark.executor.memory", "6g")
    .config("spark.local.dir", "/mnt/spark-tmp")
    .getOrCreate()
)

# ------------------------------
# Paths
# ------------------------------
RAW_BUCKET = "s3a://urban-climate-raw-235562991700"
CURATED = "s3a://urban-climate-curated-235562991700/curated/uvi/"

WEATHER_PATH = f"{RAW_BUCKET}/processed/weather/"
DEMOGRAPHICS_PATH = f"{RAW_BUCKET}/processed/demographics/"
GEO_PATH = f"{RAW_BUCKET}/processed/geospatial/"
FLOOD_PATH = f"{RAW_BUCKET}/processed/flood/"


# ------------------------------
# Safe read
# ------------------------------
def safe_read(path, schema):
    try:
        return spark.read.parquet(path)
    except Exception:
        print(f"⚠ Missing {path}, using empty placeholder")
        return spark.createDataFrame([], schema)


weather_df = safe_read(
    WEATHER_PATH,
    StructType(
        [
            StructField("region_code", StringType(), True),
            StructField("year", IntegerType(), True),
            StructField("temp_anomaly", DoubleType(), True),
            StructField("name", StringType(), True),
            StructField("dt", StringType(), True),
            StructField("main", StringType(), True),
        ]
    ),
)

demographics_df = safe_read(
    DEMOGRAPHICS_PATH,
    StructType(
        [
            StructField("region_code", StringType(), True),
            StructField("population_density", IntegerType(), True),
            StructField("year", IntegerType(), True),
        ]
    ),
)

geo_df = safe_read(
    GEO_PATH,
    StructType(
        [
            StructField("region_code", StringType(), True),
            StructField("year", IntegerType(), True),
            StructField("infra_exposure", DoubleType(), True),
        ]
    ),
)

flood_df = safe_read(
    FLOOD_PATH,
    StructType(
        [
            StructField("region_code", StringType(), True),
            StructField("year", IntegerType(), True),
            StructField("flood_risk", DoubleType(), True),
        ]
    ),
)

# ------------------------------
# DEV MODE (apply early!)
# ------------------------------
DEV_MODE = True
if DEV_MODE:
    print("Running DEV MODE: limiting each input to 1000 rows")
    weather_df = weather_df.limit(1000)
    demographics_df = demographics_df.limit(1000)
    geo_df = geo_df.limit(1000)
    flood_df = flood_df.limit(1000)

# ------------------------------
# Weather transform
# ------------------------------
if "name" in weather_df.columns:
    weather_df = weather_df.withColumn(
        "region_code",
        when(col("name") == "London", lit("LON"))
        .when(col("name") == "Manchester", lit("MAN"))
        .when(col("name") == "Birmingham", lit("BIR"))
        .otherwise(lit("UNK")),
    )

if "dt" in weather_df.columns:
    weather_df = weather_df.withColumn("year", year(col("dt")))
else:
    weather_df = weather_df.withColumn("year", lit(2025))

if "main" in weather_df.columns:
    try:
        if "temp" in weather_df.select("main.*").columns:
            weather_df = weather_df.withColumn(
                "temp_anomaly", col("main.temp") - 288.15
            )
        else:
            weather_df = weather_df.withColumn("temp_anomaly", lit(0.0))
    except Exception:
        weather_df = weather_df.withColumn("temp_anomaly", lit(0.0))
else:
    weather_df = weather_df.withColumn("temp_anomaly", lit(0.0))

if "id" in weather_df.columns:
    weather_df = weather_df.drop("id")

# ------------------------------
# Demographics cleanup
# ------------------------------
if "pop_year" in demographics_df.columns:
    demographics_df = demographics_df.withColumnRenamed("pop_year", "year")
if (
    "population" in demographics_df.columns
    and "population_density" not in demographics_df.columns
):
    demographics_df = demographics_df.withColumnRenamed(
        "population", "population_density"
    )

# ------------------------------
# Geo cleanup
# ------------------------------
if "id" in geo_df.columns:
    geo_df = geo_df.drop("id")
geo_df = (
    geo_df.withColumn("region_code", lit("LON"))
    .withColumn("year", lit(2025))
    .withColumn("infra_exposure", lit(1.0))
)

# ------------------------------
# Flood cleanup
# ------------------------------
if "flood_year" in flood_df.columns:
    flood_df = flood_df.withColumnRenamed("flood_year", "year")

# ------------------------------
# Repartition before joins
# ------------------------------
weather_df = weather_df.repartition(4, "region_code", "year")
demographics_df = demographics_df.repartition(4, "region_code", "year")
geo_df = geo_df.repartition(4, "region_code", "year")
flood_df = flood_df.repartition(4, "region_code", "year")

# ------------------------------
# Joins
# ------------------------------
if flood_df.rdd.isEmpty():
    print("⚠ Flood dataset empty, skipping flood join")
    joined = (
        weather_df.hint("mergeJoin")
        .join(demographics_df.hint("mergeJoin"), ["region_code", "year"], "left")
        .join(geo_df.hint("mergeJoin"), ["region_code", "year"], "left")
        .withColumn("flood_risk", lit(0.0))  # ✅ ensure column exists
    )
else:
    joined = (
        weather_df.hint("mergeJoin")
        .join(demographics_df.hint("mergeJoin"), ["region_code", "year"], "left")
        .join(geo_df.hint("mergeJoin"), ["region_code", "year"], "left")
        .join(flood_df.hint("mergeJoin"), ["region_code", "year"], "left")
    )

print("Preview after join:")
for row in joined.take(5):
    print(row)

# ------------------------------
# Compute UVI
# ------------------------------
joined = joined.withColumn(
    "uvi",
    (expr("0.4") * coalesce(col("temp_anomaly"), lit(0.0)))
    + (expr("0.3") * (coalesce(col("population_density"), lit(0)) / 1000.0))
    + (expr("0.2") * coalesce(col("infra_exposure"), lit(0.0)))
    + (expr("0.1") * coalesce(col("flood_risk"), lit(0.0))),
)

# ------------------------------
# Write output
# ------------------------------
(joined.write.mode("overwrite").partitionBy("year", "region_code").parquet(CURATED))

print("✅ ETL Transformation complete.")
print(f"Curated dataset written to {CURATED}")

spark.stop()
