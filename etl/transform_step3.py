import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, round, lit, count

# ---------- Spark Setup ----------
spark = (
    SparkSession.builder.appName("UrbanClimateStep3")
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    .config(
        "spark.hadoop.fs.s3a.aws.credentials.provider",
        "com.amazonaws.auth.DefaultAWSCredentialsProviderChain",
    )
    .config(
        "spark.jars.packages",
        "org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262",
    )
    .getOrCreate()
)

# ---------- Config ----------
RAW_BUCKET = os.getenv("RAW_BUCKET", "urban-climate-raw-235562991700")

PROCESSED_PREFIX_WEATHER = "processed/weather/"
PROCESSED_PREFIX_GEO = "processed/geospatial/cleaned/"
CURATED_PREFIX = "curated/uvi/"

# ---------- Load Processed Data ----------
print("Reading processed weather...")
df_weather = spark.read.parquet(f"s3a://{RAW_BUCKET}/{PROCESSED_PREFIX_WEATHER}")

print("Reading processed geospatial...")
df_geo = spark.read.parquet(f"s3a://{RAW_BUCKET}/{PROCESSED_PREFIX_GEO}")

# ---------- Cleaning ----------
# Weather: drop rows without dt, coord.lat/lon
df_weather_clean = (
    df_weather.dropna(subset=["dt", "coord"])
    .withColumn("lat", col("coord.lat"))
    .withColumn("lon", col("coord.lon"))
)

# Flatten nested fields for Redshift
df_weather_flat = (
    df_weather_clean.withColumn("clouds_all", col("clouds.all"))
    .withColumn("main_temp", col("main.temp"))
    .withColumn("main_temp_min", col("main.temp_min"))
    .withColumn("main_temp_max", col("main.temp_max"))
    .withColumn("main_humidity", col("main.humidity"))
    .withColumn("wind_speed", col("wind.speed"))
    .withColumn("wind_deg", col("wind.deg"))
    .withColumn("weather_main", col("weather").getItem(0).getField("main"))
    .withColumn("weather_desc", col("weather").getItem(0).getField("description"))
    .drop("coord", "clouds", "main", "wind", "weather", "sys")  # drop nested structs
)

# Geospatial: ensure lat/lon exist
df_geo_clean = df_geo.dropna(subset=["lat", "lon"])

# Round coordinates to ~0.01 for coarse join
df_weather_flat = df_weather_flat.withColumn(
    "lat_round", round(col("lat"), 2)
).withColumn("lon_round", round(col("lon"), 2))

df_geo_clean = df_geo_clean.withColumn("lat_round", round(col("lat"), 2)).withColumn(
    "lon_round", round(col("lon"), 2)
)

# ---------- Join ----------
df_joined = df_weather_flat.join(
    df_geo_clean, on=["lat_round", "lon_round"], how="inner"
)

print(f"Joined dataset count: {df_joined.count()} rows")

# ---------- Compute UVI (dummy metric) ----------
# Example: UVI = number of nearby geo nodes × 0.1
df_uvi = (
    df_joined.groupBy("lat_round", "lon_round")
    .agg(count("*").alias("geo_density"))
    .withColumn("uvi", col("geo_density") * lit(0.1))
)

# ---------- Write to Curated ----------
out_path = f"s3a://{RAW_BUCKET}/{CURATED_PREFIX}"
df_uvi.write.mode("overwrite").parquet(out_path)

print(f"Curated UVI dataset written to {out_path}")
