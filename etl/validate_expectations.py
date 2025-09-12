import great_expectations as ge
from pyspark.sql import SparkSession

# ============================================================
# Spark Session with Hadoop AWS packages
# ============================================================
spark = (
    SparkSession.builder.appName("ValidateCuratedWithGE")
    .config(
        "spark.jars.packages",
        "org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262",
    )
    .getOrCreate()
)

# Use AWS profile credentials from ~/.aws/credentials
hadoop_conf = spark._jsc.hadoopConfiguration()
hadoop_conf.set(
    "fs.s3a.aws.credentials.provider",
    "com.amazonaws.auth.profile.ProfileCredentialsProvider",
)
hadoop_conf.set("fs.s3a.endpoint", "s3.eu-west-2.amazonaws.com")

# ============================================================
# Paths
# ============================================================
CURATED_PATH = "s3a://urban-climate-raw-235562991700/curated/urban_vulnerability/"

# ============================================================
# Load curated dataset
# ============================================================
print(f"Reading curated dataset from {CURATED_PATH}...")
df = spark.read.parquet(CURATED_PATH)

# Wrap with Great Expectations
gdf = ge.dataset.SparkDFDataset(df)

# ============================================================
# Expectations
# ============================================================
gdf.expect_column_to_exist("region_code")
gdf.expect_column_to_exist("year")

gdf.expect_column_values_to_not_be_null("population")
gdf.expect_column_values_to_be_between("population", min_value=1000, max_value=20000000)

gdf.expect_column_values_to_not_be_null("uvi")
gdf.expect_column_values_to_be_between("uvi", min_value=0, max_value=5000)

# ============================================================
# Validation Results
# ============================================================
results = gdf.validate()
print("\n===== Great Expectations Validation Results =====")
print(results)
