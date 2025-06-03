import ee
import requests
from PIL import Image
from io import BytesIO
import base64
from openai import OpenAI
from datetime import datetime
from pathlib import Path
import geopandas as gpd

ee.Initialize()
client = OpenAI()

# download earth engine thumbnail
def download_ee_image(image, region, out_path, vis_params, dimensions=512):
    url = image.visualize(**vis_params).getThumbURL({
        'region': region,
        'dimensions': dimensions,
        'format': 'png'
    })
    response = requests.get(url)
    Image.open(BytesIO(response.content)).save(out_path)
    return out_path

# run sentinel and gedi export
def download_visuals(lat, lon, sentinel_path, gedi_path):
    point = ee.Geometry.Point(lon, lat)
    bounds = point.buffer(500).bounds()

    # sentinel-2 composite
    s2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
        .filterBounds(point) \
        .filterDate("2020-01-01", "2024-12-31") \
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 10)) \
        .sort("CLOUDY_PIXEL_PERCENTAGE") \
        .first() \
        .select(["B4", "B3", "B2"])
    sentinel_scene_id = s2.get("system:index").getInfo()

    download_ee_image(
        image=s2,
        region=bounds,
        out_path=sentinel_path,
        vis_params={'min': 0, 'max': 3000}
    )

    # gedi rh98
    gedi = ee.Image("LARSE/GEDI/GRIDDEDVEG_002/V1/1KM/gediv002_rh-98-a0_vf_20190417_20230316")
    gedi_med = gedi.select("median").updateMask(gedi.select("countf").gte(10))
    download_ee_image(
        image=gedi_med,
        region=bounds,
        out_path=gedi_path,
        vis_params={'min': 3, 'max': 40, 'palette': ['#d73027', '#fee08b', '#1a9850']}
    )

    return sentinel_scene_id, "gediv002_rh-98-a0_vf_20190417_20230316"

# base64 encode image and call gpt-4o
def analyze_image_with_openai(image_path, prompt_text, model="gpt-4o"):
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    response = client.chat.completions.create(
        model=model,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt_text},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/png;base64,{b64}"}
                }
            ]
        }],
        max_tokens=800
    )
    return response.choices[0].message.content.strip()

# paths
sentinel_img = Path("openai2z/data/processed/sentinel_rgb.png")
gedi_img = Path("openai2z/data/processed/gedi_rh98.png")
log_file = Path("openai2z/logs/llm_output.txt")
log_file.parent.mkdir(parents=True, exist_ok=True)

# run
brazil_sites = gpd.read_file("openai2z/data/processed/geoglyph_sites_points.geojson")

# look at one point from my existing sites dataset. 
abuna_chico = brazil_sites[brazil_sites["name"] == "abuc1"].iloc[0]
lat, lon = float(abuna_chico["latitude"]), float(abuna_chico["longitude"])

sentinel_scene, gedi_scene = download_visuals(lat, lon, sentinel_img, gedi_img)

base_dir = Path(__file__).resolve().parent

# analyze sentinel
sentinel_prompt = (base_dir / "openai2z/prompts/sentinel_prompt.txt").read_text()
sentinel_out = analyze_image_with_openai(sentinel_img, sentinel_prompt)

# analyze gedi
gedi_prompt = (base_dir / "openai2z/prompts/gedi_prompt.txt").read_text()
gedi_out = analyze_image_with_openai(gedi_img, gedi_prompt)

# log everything
with open(log_file, "a", encoding="utf-8") as f:
    f.write(f"[{datetime.now().isoformat()}] model=gpt-4o\n")
    f.write(f"sentinel_scene={sentinel_scene}\n")
    f.write(f"gedi_scene={gedi_scene}\n\n")
    f.write("--- Sentinel Output ---\n")
    f.write(sentinel_out + "\n\n")
    f.write("--- GEDI Output ---\n")
    f.write(gedi_out + "\n\n")


# print model and scene info
print(f"model used: {model_name}")
print(f"sentinel-2 scene ID: {sentinel_scene}")
print(f"gedi scene ID: {gedi_scene}")
