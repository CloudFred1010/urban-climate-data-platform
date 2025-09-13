from pyspark.sql import SparkSession

spark = (
    SparkSession.builder.appName("CompactGeospatial")
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

# Read existing parquet
df = spark.read.parquet("s3a://urban-climate-raw-235562991700/processed/geospatial/")

# Compact to 10 output files
df.coalesce(10).write.mode("overwrite").parquet(
    "s3a://urban-climate-raw-235562991700/processed/geospatial/cleaned/"
)

print("Compaction finished → written to geospatial/cleaned/")
