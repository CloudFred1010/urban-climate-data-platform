import subprocess
import geopandas as gpd
import boto3

# Config
S3_BUCKET = "urban-climate-raw-235562991700"
RAW_KEY = "raw/geospatial/london_20250912_valid.osm.pbf"
OUTPUT_KEY = "processed/geospatial/standardised/london_boundaries.parquet"

LOCAL_PBF = "/tmp/london.osm.pbf"
LOCAL_BBOX_PBF = "/tmp/london_bbox.osm.pbf"
LOCAL_GPKG = "/tmp/london_boundaries.gpkg"
LOCAL_PARQUET = "/tmp/london_boundaries.parquet"

# Download raw OSM extract from S3
print("Downloading raw OSM extract from S3...")
s3 = boto3.client("s3")
s3.download_file(S3_BUCKET, RAW_KEY, LOCAL_PBF)

# Bounding box for Greater London
london_bbox = "-0.489,51.28,0.236,51.686"

# Trim with osmium
print("Trimming to London bounding box with osmium...")
subprocess.run(
    ["osmium", "extract", "-b", london_bbox, LOCAL_PBF, "-o", LOCAL_BBOX_PBF],
    check=True,
)

# Convert PBF → GeoPackage with ogr2ogr
print("Converting bbox PBF → GeoPackage with ogr2ogr...")
subprocess.run(
    ["ogr2ogr", "-f", "GPKG", LOCAL_GPKG, LOCAL_BBOX_PBF, "multipolygons"], check=True
)

# Convert GeoPackage → Parquet
print("Reading GeoPackage with GeoPandas...")
gdf = gpd.read_file(LOCAL_GPKG)

if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
    print("Reprojecting to EPSG:4326...")
    gdf = gdf.to_crs(epsg=4326)

print("Saving to Parquet...")
gdf.to_parquet(LOCAL_PARQUET, index=False)

# Upload back to S3
print("Uploading Parquet to S3...")
s3.upload_file(LOCAL_PARQUET, S3_BUCKET, OUTPUT_KEY)

print(f"Geospatial data written to s3://{S3_BUCKET}/{OUTPUT_KEY}")
