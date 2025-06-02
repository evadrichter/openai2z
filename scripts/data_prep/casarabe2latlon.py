import os
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from pyproj import Transformer

def convert_casarabe():
    base_dir = os.path.dirname(__file__)
    input_csv = os.path.join(base_dir, "openai2z", "data", "raw", "casarabe_utm.csv")
    output_geojson = os.path.join(base_dir, "openai2z", "data", "processed", "casarabe_sites.geojson")

    df = pd.read_csv(input_csv)
    transformer = Transformer.from_crs("EPSG:32720", "EPSG:4326", always_xy=True)

    coords = [transformer.transform(x, y) for x, y in zip(df["UTM X (Easting)"], df["UTM Y (Northing)"])]
    df["geometry"] = [Point(lon, lat) for lon, lat in coords]

    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")
    os.makedirs(os.path.dirname(output_geojson), exist_ok=True)
    gdf.to_file(output_geojson, driver="GeoJSON")

    print("Saved:", output_geojson)

if __name__ == "__main__":
    convert_casarabe()
