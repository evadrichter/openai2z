import requests
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=r"C:\Users\evari\OneDrive\Dokumente\OpenAI2Z\openai2z\.env")

api_key = os.getenv("OPENTOPO_API_KEY")
if not api_key:
    raise RuntimeError("No OPENTOPO_API_KEY found.")

# 12° S, 53° W
# -12.000000, -53.000000

# Define your location and bounding box (in degrees)
latitude = -8.4691
longitude = -64.3331
buffer_deg = 0.5  # Small buffer ~100m depending on latitude

bbox = f"{longitude-buffer_deg},{latitude-buffer_deg},{longitude+buffer_deg},{latitude+buffer_deg}"

# OpenTopography API endpoint
url = "https://portal.opentopography.org/API/globaldem"
params = {
    "demtype": "AW3D30",  # or try 'COP30', 'AW3D30', 'NASADEM'
    "south": latitude - buffer_deg,
    "north": latitude + buffer_deg,
    "west": longitude - buffer_deg,
    "east": longitude + buffer_deg,
    "outputFormat": "GTiff",
    "API_Key": api_key
}

# Make the request
url = "https://portal.opentopography.org/API/globaldem"
print(" Requesting DEM tile from OpenTopography...")

response = requests.get(url, params=params)

# Handle response
if response.status_code == 200 and "Content-Disposition" in response.headers:
    filename = response.headers["Content-Disposition"].split("filename=")[-1]
    abs_str = r"C:\Users\evari\OneDrive\Dokumente\OpenAI2Z"
    file_path = os.path.join(abs_str, "openai2z", "data", "raw", filename)
    with open(file_path, "wb") as f:
        f.write(response.content)
    print(f"DEM saved as: {file_path}")
else:
    print(f"Failed to retrieve data: {response.status_code}\n{response.text}")