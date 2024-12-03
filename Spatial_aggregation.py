import os
import rasterio
import numpy as np
import pandas as pd

# Paths
input_folder = "./DR_climate"  # Replace with the folder containing your TIF files
output_csv = "./spatial_aggregation.csv"         # Replace with the desired output CSV file path
output_raster_folder = "./annual_aggregation"  # Replace with the folder to save aggregated rasters

# Ensure output raster folder exists
os.makedirs(output_raster_folder, exist_ok=True)

# Function to extract metadata from file name
def parse_filename(filename):
    parts = filename.lower().split("_")  # Assuming underscore-separated file name
    data_type = None
    month = None

    for part in parts:
        if "prec" in part:
            data_type = "Precipitation"
        elif "tavg" in part:
            data_type = "Mean Temperature"
        elif "tmin" in part:
            data_type = "Min Temperature"
        elif "tmax" in part:
            data_type = "Max Temperature"
        
        # if part.isdigit() and len(part) == 2:  # Assuming month is two digits
        #     month = part
        month=filename[-6:-4]
    return data_type, month

# Function to calculate mean value of raster
def calculate_raster_mean(tif_path):
    with rasterio.open(tif_path) as src:
        array = src.read(1)  # Read the first band
        mean_value = array[array != src.nodata].mean()  # Exclude no-data values
        return mean_value

def aggregate_rasters_by_type(file_paths, output_path):
    rasters = []
    meta = None

    # Read all rasters and stack them
    for file_path in file_paths:
        with rasterio.open(file_path) as src:
            rasters.append(src.read(1))
            if meta is None:
                meta = src.meta.copy()

    # Calculate mean raster
    stacked_rasters = np.stack(rasters, axis=0)
    mean_raster = np.nanmean(np.where(stacked_rasters != meta['nodata'], stacked_rasters, np.nan), axis=0)

    # Update metadata and write to a new file
    meta.update({
        "dtype": "float32",
        "count": 1
    })
    with rasterio.open(output_path, "w", **meta) as dest:
        dest.write(mean_raster, 1)

# Main script
if __name__ == "__main__":
    results = {}
    data_type_files = {}

    # Process each TIF file in the folder
    for tif_file in os.listdir(input_folder):
        if tif_file.endswith(".tif"):
            tif_path = os.path.join(input_folder, tif_file)
            
            data_type, month = parse_filename(tif_file)
            if data_type and month:
                # Calculate mean value
                mean_value = calculate_raster_mean(tif_path)

                # Store mean value in results dictionary
                if month not in results:
                    results[month] = {}
                results[month][data_type] = mean_value

                # Group files by data type
                if data_type not in data_type_files:
                    data_type_files[data_type] = []
                data_type_files[data_type].append(tif_path)

    # Generate average rasters by data type
    for data_type, file_paths in data_type_files.items():
        output_raster_path = os.path.join(output_raster_folder, f"{data_type.replace(' ', '_').lower()}_aggregated.tif")
        print(f"Aggregating rasters for {data_type} into {output_raster_path}...")
        aggregate_rasters_by_type(file_paths, output_raster_path)

    # Convert results dictionary to DataFrame
    df = pd.DataFrame.from_dict(results, orient="index").sort_index()
    df.index.name = "Month"
    df.columns.name = "Variable"

    # Save to CSV
    df.to_csv(output_csv)

    print(f"Results saved to {output_csv}")
    print(f"Aggregated rasters saved to {output_raster_folder}")
