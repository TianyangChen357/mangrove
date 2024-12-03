import geopandas as gpd
import rasterio
from rasterio.mask import mask
import os
from pathlib import Path

# Paths
shp_path = "mangrove_boundary.shp"  # Replace with the path to your KML file
tif_folder = "./global_climate"      # Replace with the folder path containing TIF files
output_folder = "./DR_climate"     # Replace with the folder path to save extracted rasters

# Load KML file
def load_kml_boundary(shp_path):
    gdf = gpd.read_file(shp_path)
    gdf = gdf.to_crs("EPSG:4326")  # Ensure CRS is consistent with TIF files
    return gdf

# Extract raster by boundary
def extract_raster(tif_path, boundary_gdf, output_path):
    with rasterio.open(tif_path) as src:
        # Mask raster using the boundary geometry
        boundary_geom = [boundary_gdf.geometry[0]]  # Assumes single polygon boundary
        out_image, out_transform = mask(src, boundary_geom, crop=True)
        out_meta = src.meta.copy()

        # Update metadata for the output raster
        out_meta.update({
            "driver": "GTiff",
            "height": out_image.shape[1],
            "width": out_image.shape[2],
            "transform": out_transform
        })

        # Write the masked raster to a new file
        with rasterio.open(output_path, "w", **out_meta) as dest:
            dest.write(out_image)

# Main script
if __name__ == "__main__":
    # Load KML boundary
    boundary_gdf = load_kml_boundary(shp_path)
    
    # Ensure the output folder exists
    Path(output_folder).mkdir(parents=True, exist_ok=True)
    
    # Process each TIF file in the folder
    for tif_file in os.listdir(tif_folder):
        if tif_file.endswith(".tif"):
            tif_path = os.path.join(tif_folder, tif_file)
            output_path = os.path.join(output_folder, f"DR_np_{tif_file}")
            
            print(f"Processing {tif_file}...")
            extract_raster(tif_path, boundary_gdf, output_path)
    
    print("Extraction completed.")
