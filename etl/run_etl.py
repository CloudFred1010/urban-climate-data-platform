#!/usr/bin/env python3
"""
Urban Climate Data Platform - ETL Step 3
----------------------------------------
Transforms raw weather, demographics, geo, and flood zone data
into a curated Urban Vulnerability Index (UVI) dataset.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, expr, year, lit, when
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
        "org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262",
    )
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    .config(
        "spark.hadoop.fs.s3a.aws.credentials.provider",
        "com.amazonaws.auth.DefaultAWSCredentialsProviderChain",
    )
    .config("spark.sql.shuffle.partitions", "50")  # fewer shuffle partitions
    .config("spark.sql.autoBroadcastJoinThreshold", "-1")  # disable broadcast joins
    .config("spark.sql.join.preferSortMergeJoin", "true")  # prefer sort-merge joins
    .config("spark.driver.memory", "3g")
    .config("spark.executor.memory", "3g")
    .getOrCreate()
)

# Ensure settings are applied after session creation
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", -1)
spark.conf.set("spark.sql.join.preferSortMergeJoin", True)

# ------------------------------
# Input / Output Paths
# ------------------------------
RAW_BUCKET = "s3a://urban-climate-raw-235562991700"
CURATED_PATH = "s3a://urban-climate-processed/curated/urban_vulnerability/"

WEATHER_PATH = f"{RAW_BUCKET}/processed/weather/"
DEMOGRAPHICS_PATH = f"{RAW_BUCKET}/processed/demographics/"
GEO_PATH = f"{RAW_BUCKET}/processed/geospatial/"
FLOOD_PATH = f"{RAW_BUCKET}/processed/flood/"

# ------------------------------
# Load Datasets
# ------------------------------
weather_raw = spark.read.parquet(WEATHER_PATH)
demographics_df = spark.read.parquet(DEMOGRAPHICS_PATH)
geo_df = spark.read.parquet(GEO_PATH)

# Flood fallback
try:
    flood_df = spark.read.parquet(FLOOD_PATH)
except Exception:
    print("Flood data not found, using empty placeholder")
    flood_schema = StructType(
        [
            StructField("region_code", StringType(), True),
            StructField("year", IntegerType(), True),
            StructField("flood_risk", DoubleType(), True),
        ]
    )
    flood_df = spark.createDataFrame([], flood_schema)

# ------------------------------
# Weather Normalisation
# ------------------------------
weather_df = weather_raw.withColumn(
    "region_code",
    when(col("name") == "London", lit("LON"))
    .when(col("name") == "Manchester", lit("MAN"))
    .when(col("name") == "Birmingham", lit("BIR"))
    .otherwise(lit("UNK")),
)

weather_df = weather_df.withColumn("year", year(col("dt")))
weather_df = weather_df.withColumn("temp_anomaly", col("main.temp") - lit(288.15))

# ------------------------------
# Standardise Other Datasets
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

geo_df = (
    geo_df.withColumn("region_code", lit("LON"))  # TODO: real mapping
    .withColumn("year", lit(2025))
    .withColumn("infra_exposure", lit(1.0))
)

if "flood_year" in flood_df.columns:
    flood_df = flood_df.withColumnRenamed("flood_year", "year")

# Drop duplicate IDs if present
if "id" in weather_df.columns:
    weather_df = weather_df.drop("id")
if "id" in geo_df.columns:
    geo_df = geo_df.drop("id")

# ------------------------------
# Debugging Schemas
# ------------------------------
print("Weather schema:")
weather_df.printSchema()
print("Demographics schema:")
demographics_df.printSchema()
print("Geo schema:")
geo_df.printSchema()
print("Flood schema:")
flood_df.printSchema()

# ------------------------------
# Join Datasets (outer join for safety)
# ------------------------------
joined_df = (
    weather_df.join(demographics_df, ["region_code", "year"], "outer")
    .join(geo_df, ["region_code", "year"], "outer")
    .join(flood_df, ["region_code", "year"], "outer")
)

# ------------------------------
# Debug: Safe Sample Print
# ------------------------------
print("Sample joined rows (10 preview):")
# Using show() instead of take() to avoid collect + broadcast
joined_df.show(10, truncate=False)

# ------------------------------
# Compute UVI (Weighted Formula)
# ------------------------------
population_weight = 0.4
weather_weight = 0.3
flood_weight = 0.2
infra_weight = 0.1

joined_df = joined_df.withColumn(
    "uvi",
    (expr(str(population_weight)) * col("population_density"))
    + (expr(str(weather_weight)) * col("temp_anomaly"))
    + (expr(str(flood_weight)) * col("flood_risk"))
    + (expr(str(infra_weight)) * col("infra_exposure")),
)

# ------------------------------
# Write Curated Dataset
# ------------------------------
(
    joined_df.write.mode("overwrite")
    .partitionBy("region_code", "year")
    .parquet(CURATED_PATH)
)

print("✅ ETL Transformation complete.")
print(f"Curated dataset written to {CURATED_PATH}")

spark.stop()
