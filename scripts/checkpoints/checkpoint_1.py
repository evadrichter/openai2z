#!/usr/bin/env python3

import os
import ee
import base64
import requests
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime

# --------------------------------------------------------------------
# ENV SETUP
# --------------------------------------------------------------------
load_dotenv()
client = OpenAI()
if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError("Missing OPENAI_API_KEY in .env")

# --------------------------------------------------------------------
# INIT EE
# --------------------------------------------------------------------
def initialize_ee():
    try:
        ee.Initialize()
    except Exception:
        raise RuntimeError("Run `earthengine authenticate` to proceed.")

initialize_ee()

# --------------------------------------------------------------------
# SETTINGS
# --------------------------------------------------------------------
lat, lon = -9.319740, -58.890934  # Amazon
model_name = "gpt-4o"
out_dir = Path("checkpoint_outputs")
out_dir.mkdir(exist_ok=True)
image_file = out_dir / "sentinel2.png"

# --------------------------------------------------------------------
# DOWNLOAD THUMBNAIL
# --------------------------------------------------------------------
def download_sentinel_thumbnail(lat, lon, path):
    pt = ee.Geometry.Point([lon, lat])
    start = ee.Date(datetime.utcnow()).advance(-30, "day")
    end = ee.Date(datetime.utcnow())

    col = ee.ImageCollection("COPERNICUS/S2_SR") \
        .filterBounds(pt) \
        .filterDate(start, end) \
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 10))

    img = ee.Image(col.first())
    img_id = img.get("system:id").getInfo()

    url = img.getThumbURL({
        "bands": ["B4", "B3", "B2"],
        "min": 0,
        "max": 3000,
        "dimensions": 512,
        "region": img.geometry().bounds().getInfo()
    })

    print(f"Downloading image from: {url}")
    r = requests.get(url)
    with open(path, "wb") as f:
        f.write(r.content)

    return img_id

# --------------------------------------------------------------------
# CALL OPENAI
# --------------------------------------------------------------------
def analyze_with_openai(image_path: Path, prompt: str, model="gpt-4o"):
    with open(image_path, "rb") as f:
        base64_image = base64.b64encode(f.read()).decode("utf-8")

    response = client.chat.completions.create(
        model=model,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/png;base64,{base64_image}"}
                }
            ]
        }],
        max_tokens=800
    )
    return response.choices[0].message.content.strip()

# --------------------------------------------------------------------
# RUN CHECKPOINT
# --------------------------------------------------------------------
if __name__ == "__main__":
    print("🚀 Running OpenAI to Z Checkpoint 1")

    # 1. Download image
    scene_id = download_sentinel_thumbnail(lat, lon, image_file)

    # 2. Call OpenAI model
    prompt = "Describe the landscape and surface features visible in this Sentinel-2 image in plain English."
    result = analyze_with_openai(image_file, prompt, model=model_name)

    # 3. Output
    print("\n✅ Model Output:")
    print(result)
    print("\n📌 Model Used:", model_name)
    print("🛰️  Sentinel-2 Scene ID:", scene_id)
