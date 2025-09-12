import os
import boto3
import requests
from datetime import datetime, timezone


# ============================
# Fetch demographics data (WorldPop UK population density .tif)
# ============================
def fetch_demographics():
    url = "https://hub.worldpop.org/geodata/summary?id=49412&format=geotiff"
    # Or if direct link is provided, use that exact link to the .tif file
    resp = requests.get(url, stream=True)
    resp.raise_for_status()
    return resp.content, "gbr_population_density_2020"


# ============================
# Write to S3
# ============================
def write_to_s3(bucket, prefix, data, filename):
    s3 = boto3.client("s3")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    key = f"{prefix}{filename}_{timestamp}.tif"
    s3.put_object(Bucket=bucket, Key=key, Body=data, ContentType="image/tiff")
    print(f"Uploaded: s3://{bucket}/{key}")


if __name__ == "__main__":
    bucket = os.environ.get("S3_BUCKET_NAME", "urban-climate-raw-235562991700")
    prefix = "raw/demographics/"
    data, filename = fetch_demographics()
    write_to_s3(bucket, prefix, data, filename)
