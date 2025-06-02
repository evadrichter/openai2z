from bs4 import BeautifulSoup
import geopandas as gpd
from shapely.geometry import Point, Polygon, LineString
import pandas as pd
import os

base_dir = os.path.dirname(__file__)  
file_path = os.path.join(base_dir, "openai2z/data/raw/amazon_geoglyphs.kml")

# load kml from data/raw
with open(file_path, "r", encoding="utf-8") as f:
    kml_data = f.read()


# parse using bs4
soup = BeautifulSoup(kml_data, "xml")
placemarks = soup.find_all("Placemark")
soup = BeautifulSoup(kml_data, "xml")
placemarks = soup.find_all("Placemark")

point_features = []
shape_features = []

for p in placemarks:
    name = p.find("name").text.strip() if p.find("name") else None
    desc = p.find("description").text.strip() if p.find("description") else None
    coord_tag = p.find("coordinates")

    if not coord_tag:
        continue

    raw_coords = coord_tag.text.strip()

    try:
        # handling multiple coordinates
        coord_list = raw_coords.split()
        coords = [tuple(map(float, c.split(",")[:2])) for c in coord_list]

        if len(coords) == 1:
            # point handling
            lon, lat = coords[0]
            geometry = Point(lon, lat)
            point_features.append({
                "name": name,
                "description": desc,
                "longitude": lon,
                "latitude": lat,
                "geometry": geometry
            })

        elif coords[0] == coords[-1] and len(coords) >= 4:
            # polygon handling
            geometry = Polygon(coords)
            shape_features.append({
                "name": name,
                "description": desc,
                "geometry": geometry
            })

        else:
            # linestring handling
            geometry = LineString(coords)
            shape_features.append({
                "name": name,
                "description": desc,
                "geometry": geometry
            })

    except Exception as e:
        print(f"Can't process coordinate: {raw_coords[:120]}...\nReason: {e}\n")

gglyphs_points = gpd.GeoDataFrame(point_features, geometry="geometry", crs="EPSG:4326")
gglyphs_shapes = gpd.GeoDataFrame(shape_features, geometry="geometry", crs="EPSG:4326")

# save in folder
points_path = os.path.join(base_dir, "openai2z/data/processed/geoglyph_sites_points.kml")
shapes_path = os.path.join(base_dir, "openai2z/data/processed/geoglyph_sites_shapes.kml")

gglyphs_points.to_file(points_path, driver="GeoJSON")
gglyphs_shapes.to_file(shapes_path, driver="GeoJSON")


print("Succesfully saved it all to the folders.")
