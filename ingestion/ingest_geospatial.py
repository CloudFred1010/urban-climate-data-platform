import os
import json
import boto3
import requests
from datetime import datetime


def get_secret(secret_name, region="eu-west-2"):
    client = boto3.client("secretsmanager", region_name=region)
    response = client.get_secret_value(SecretId=secret_name)
    secret_str = response["SecretString"]
    secret = json.loads(secret_str)
    return secret.get("api_key")


def fetch_weather(api_key, city="London"):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}"
    resp = requests.get(url)
    if resp.status_code != 200:
        raise RuntimeError(
            f"Failed to fetch weather data: {resp.status_code} {resp.text}"
        )
    return resp.json()


def write_to_s3(bucket, prefix, data, city):
    s3 = boto3.client("s3")
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    key = f"{prefix}{city}_{timestamp}.json"
    s3.put_object(Bucket=bucket, Key=key, Body=json.dumps(data))
    print(f"Uploaded: s3://{bucket}/{key}")


if __name__ == "__main__":
    #  Always return just the api_key string
    api_key = get_secret("openweathermap-api-key")

    # Test fetch
    weather_data = fetch_weather(api_key, city="London")

    # Upload to S3
    bucket = os.environ.get("S3_BUCKET_NAME", "urban-climate-raw-235562991700")
    prefix = "raw/weather/"
    write_to_s3(bucket, prefix, weather_data, city="London")
