import geopandas as gpd
import boto3

# Paths
LOCAL_GPKG = "london_boundaries.gpkg"
LOCAL_PARQUET = "london_boundaries.parquet"
S3_BUCKET = "urban-climate-raw-235562991700"
S3_KEY = "processed/geospatial/standardised/london_boundaries.parquet"

# Load from GeoPackage
print("Reading GeoPackage...")
gdf = gpd.read_file(LOCAL_GPKG)

# Reproject to EPSG:4326 (if not already)
if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
    print("Reprojecting to EPSG:4326...")
    gdf = gdf.to_crs(epsg=4326)

# Save as Parquet
print("Saving to Parquet...")
gdf.to_parquet(LOCAL_PARQUET, index=False)

# Upload to S3
print("Uploading to S3...")
s3 = boto3.client("s3")
s3.upload_file(LOCAL_PARQUET, S3_BUCKET, S3_KEY)

print(f"Geospatial data written to s3://{S3_BUCKET}/{S3_KEY}")
