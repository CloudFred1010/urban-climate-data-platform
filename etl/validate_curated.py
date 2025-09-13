from pyspark.sql import SparkSession

# ---------- Spark Setup ----------
spark = (
    SparkSession.builder.appName("ValidateCurated")
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

# ---------- Load curated data ----------
df_curated = spark.read.parquet(
    "s3a://urban-climate-raw-235562991700/curated/urban_vulnerability/"
)

print(" Schema:")
df_curated.printSchema()

print(" Sample rows:")
df_curated.show(5, truncate=False)

print(f"Total rows: {df_curated.count()}")
