from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, year, from_unixtime, last
from pyspark.sql.window import Window

# ============================================================
# Initialise Spark with Hadoop AWS packages
# ============================================================
spark = (
    SparkSession.builder.appName("JoinDatasets_UVI")
    .config(
        "spark.jars.packages",
        "org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262",
    )
    .getOrCreate()
)

# Configure Hadoop S3A to use the default AWS credentials chain
hadoop_conf = spark._jsc.hadoopConfiguration()
hadoop_conf.set(
    "fs.s3a.aws.credentials.provider",
    "com.amazonaws.auth.DefaultAWSCredentialsProviderChain",
)
hadoop_conf.set("fs.s3a.endpoint", "s3.eu-west-2.amazonaws.com")  # London region

# ============================================================
# Input & Output Paths
# ============================================================
WEATHER_PATH = "s3a://urban-climate-raw-235562991700/processed/weather/"
DEMOGRAPHICS_PATH = (
    "s3a://urban-climate-raw-235562991700/raw/demographics/london_population.csv"
)
GEO_PATH = "s3a://urban-climate-raw-235562991700/processed/geospatial/standardised/london_boundaries.parquet"

CURATED_PATH = "s3a://urban-climate-raw-235562991700/curated/urban_vulnerability/"

# ============================================================
# Load Datasets
# ============================================================
print("Reading datasets...")

weather_df = spark.read.parquet(WEATHER_PATH)

# Load demographics CSV with schema casting
demo_df = (
    spark.read.option("header", True)
    .csv(DEMOGRAPHICS_PATH)
    .withColumn("year", col("year").cast("int"))
    .withColumn("population", col("population").cast("int"))
    .withColumn("region_code", col("region_code"))  # ensure column exists
)

geo_df = spark.read.parquet(GEO_PATH)

print(f"Weather count: {weather_df.count()}")
print(f"Demographics count: {demo_df.count()}")
print(f"Geo count: {geo_df.count()}")

# ============================================================
# Normalise Weather Dataset
# ============================================================
print("Normalising weather dataset...")

weather_df = weather_df.withColumn(
    "region_code",
    when(col("name") == "London", "LON")
    .when(col("name") == "Manchester", "MAN")
    .when(col("name") == "Birmingham", "BIR"),
)

# Handle dt column type
dt_type = [
    f.dataType.simpleString() for f in weather_df.schema.fields if f.name == "dt"
][0]
print(f"Detected dt column type: {dt_type}")

if dt_type == "bigint":
    weather_df = weather_df.withColumn("year", year(from_unixtime(col("dt"))))
elif dt_type == "timestamp":
    weather_df = weather_df.withColumn("year", year(col("dt")))
else:
    raise TypeError(f"Unsupported dt type: {dt_type}")

weather_df = weather_df.dropna(subset=["region_code", "year"])
weather_df.select("name", "region_code", "year").show(10, truncate=False)

# ============================================================
# Normalise Geo Dataset
# ============================================================
print("Normalising geo dataset...")

geo_df = (
    geo_df.withColumn(
        "region_code",
        when(col("name") == "London", "LON")
        .when(col("name") == "Manchester", "MAN")
        .when(col("name") == "Birmingham", "BIR"),
    )
    .dropna(subset=["region_code"])
    .drop("name")
)

geo_df.select("region_code").distinct().show(10, truncate=False)

# ============================================================
# Align Demographics by Year
# ============================================================
print("Aligning demographics by year...")

year_range = weather_df.selectExpr(
    "min(year) as min_year", "max(year) as max_year"
).collect()[0]
min_year, max_year = year_range["min_year"], year_range["max_year"]

region_years = (
    demo_df.select("region_code")
    .distinct()
    .crossJoin(spark.range(min_year, max_year + 1).withColumnRenamed("id", "year"))
)

demo_aligned = region_years.join(demo_df, ["region_code", "year"], "left").withColumn(
    "population",
    last("population", ignorenulls=True).over(
        Window.partitionBy("region_code")
        .orderBy("year")
        .rowsBetween(Window.unboundedPreceding, 0)
    ),
)

print("After alignment, demographics covers:")
demo_aligned.groupBy("year").count().orderBy("year").show()

# ============================================================
# Join Datasets
# ============================================================
print("Joining datasets...")
joined_df = weather_df.join(demo_aligned, ["region_code", "year"], "inner").join(
    geo_df, ["region_code"], "inner"
)

# Weighted UVI calculation
joined_df = joined_df.withColumn(
    "uvi",
    (col("population") * 0.0001)  # population weight
    + (col("main.temp") * 0.001)  # penalise temp stress
    - (col("main.humidity") * 0.0005)  # adjust for humidity
    + (col("clouds.all") * 0.0002),  # factor in cloudiness
)

# ============================================================
# Write Curated Output (partitioned)
# ============================================================
print(f"Writing curated dataset to {CURATED_PATH}...")
(
    joined_df.write.mode("overwrite")
    .partitionBy("region_code", "year")
    .parquet(CURATED_PATH)
)

print("Join complete. Curated dataset ready.")
