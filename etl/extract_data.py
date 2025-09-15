#!/usr/bin/env python3
"""
etl/extract_data.py
-------------------
Phase 6 - Extract step of the ETL pipeline.
Fetches raw datasets and writes them to S3/raw (or local staging).
"""

import os
import requests

# Example: OpenWeatherMap or placeholder dataset
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../data/raw")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def extract_weather():
    url = "https://raw.githubusercontent.com/plotly/datasets/master/2016-weather-data-seattle.csv"
    resp = requests.get(url, timeout=30)
    output_file = os.path.join(OUTPUT_DIR, "weather.csv")
    with open(output_file, "wb") as f:
        f.write(resp.content)
    print(f"Extracted weather data to {output_file}")


if __name__ == "__main__":
    extract_weather()
