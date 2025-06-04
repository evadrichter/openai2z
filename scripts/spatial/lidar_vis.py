import os
import numpy as np
import matplotlib.pyplot as plt
import rasterio
from rasterio.plot import show
from matplotlib.colors import LightSource

# === Paths ===
input_tif = r"C:\Users\evari\OneDrive\Dokumente\OpenAI2Z\openai2z\data\raw\appRasterSelectAPIService1749002562294-1273778585.tif"
output_dir = r"C:\Users\evari\OneDrive\Dokumente\OpenAI2Z\openai2z\visualisation\vis-output"
os.makedirs(output_dir, exist_ok=True)

with rasterio.open(input_tif) as src:
    dem = src.read(1).astype(float)  
    nodata = src.nodata
    if nodata is not None:
        dem[dem == nodata] = np.nan
    transform = src.transform

# === Generate Hillshade ===
ls = LightSource(azdeg=315, altdeg=45)
hillshade = ls.hillshade(dem, vert_exag=1, dx=1, dy=1)

plt.imshow(hillshade, cmap='gray')
plt.title("Hillshade")
plt.axis('off')
plt.savefig(os.path.join(output_dir, "hillshade_mapinguari.png"), bbox_inches='tight', dpi=300)
plt.close()

# === Generate Slope Map ===
from scipy import ndimage

dx, dy = np.gradient(dem)
slope = np.sqrt(dx**2 + dy**2)

plt.imshow(slope, cmap='inferno')
plt.title("Slope Map")
plt.axis('off')
plt.colorbar(label="Slope gradient")
plt.savefig(os.path.join(output_dir, "slope_map_mapinguari.png"), bbox_inches='tight', dpi=300)
plt.close()

# === Generate Contour Map ===
plt.figure(figsize=(10, 8))
plt.contour(dem, levels=20, cmap='viridis', linewidths=0.5)
plt.title("Contour Map")
plt.axis('off')
plt.savefig(os.path.join(output_dir, "contours_mapinguari.png"), bbox_inches='tight', dpi=300)
plt.close()

smooth_dem = ndimage.gaussian_filter(dem, sigma=30)
lrm = dem - smooth_dem

plt.imshow(lrm, cmap='RdBu', vmin=-2, vmax=2)
plt.title("Local Relief Model")
plt.axis('off')
plt.colorbar(label='Relative Elevation (m)')
plt.savefig(os.path.join(output_dir, "local_relief_model_mapinguari.png"), bbox_inches='tight', dpi=300)
plt.close()

# === Multi-directional Hillshade ===
azimuths = [45, 135, 225, 315]  # NE, SE, SW, NW
combined_hs = np.zeros_like(dem)
for az in azimuths:
    ls = LightSource(azdeg=az, altdeg=45)
    combined_hs += ls.hillshade(dem, vert_exag=1, dx=1, dy=1)

combined_hs /= len(azimuths)  # Average them
plt.imshow(combined_hs, cmap='gray')
plt.title("Multi-directional Hillshade")
plt.axis('off')
plt.savefig(os.path.join(output_dir, "multi_hillshade_mapinguari.png"), bbox_inches='tight', dpi=300)
plt.close()

# === Elevation Color Map ===
plt.imshow(dem, cmap='terrain')
plt.title("Elevation Map")
plt.axis('off')
plt.colorbar(label="Elevation (m)")
plt.savefig(os.path.join(output_dir, "elevation_colormap_mapinguari.png"), bbox_inches='tight', dpi=300)
plt.close()

# === Aspect Map ===
aspect = np.arctan2(-dx, dy)
aspect_deg = np.degrees(aspect)
aspect_deg = (aspect_deg + 360) % 360

plt.imshow(aspect_deg, cmap='twilight')
plt.title("Aspect Map (Slope Direction)")
plt.axis('off')
plt.colorbar(label="Degrees from North")
plt.savefig(os.path.join(output_dir, "aspect_map_mapinguari.png"), bbox_inches='tight', dpi=300)
plt.close()

# === Topographic Position Index (TPI) ===
# TPI = elevation - local mean elevation (in a smaller neighborhood)
local_mean = ndimage.uniform_filter(dem, size=15)
tpi = dem - local_mean

plt.imshow(tpi, cmap='coolwarm', vmin=-5, vmax=5)
plt.title("Topographic Position Index (TPI)")
plt.axis('off')
plt.colorbar(label="TPI (m)")
plt.savefig(os.path.join(output_dir, "tpi_mapinguari.png"), bbox_inches='tight', dpi=300)
plt.close()

print("✅ Visualizations saved to:", output_dir)
