from pyspark.sql import SparkSession
from pyspark.sql.functions import col

# Initialise Spark with Hadoop AWS support
spark = (
    SparkSession.builder.appName("DemographicsCleaning")
    .config(
        "spark.jars.packages",
        "org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262",
    )
    .getOrCreate()
)

# Configure Spark to talk to S3 via s3a://
hadoop_conf = spark.sparkContext._jsc.hadoopConfiguration()
hadoop_conf.set("fs.s3.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
hadoop_conf.set(
    "fs.s3a.aws.credentials.provider",
    "com.amazonaws.auth.DefaultAWSCredentialsProviderChain",
)

# Input (raw demographics CSV from ONS)
raw_path = "s3a://urban-climate-raw-235562991700/raw/demographics/ons_population.csv"

# Output (processed zone)
processed_path = "s3a://urban-climate-raw-235562991700/processed/demographics/"

# Load raw demographics
df = spark.read.csv(raw_path, header=True, inferSchema=True)

# Basic cleaning: drop nulls, enforce schema
df_clean = (
    df.dropna(subset=["region_code", "population"])
    .withColumn("population", col("population").cast("int"))
    .withColumn("year", col("year").cast("int"))
)

# Write to processed zone as Parquet
df_clean.write.mode("overwrite").parquet(processed_path)

print(f"✅ Demographics data written to {processed_path}")
