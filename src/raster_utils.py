from pathlib import Path
from datetime import datetime
import os

import geopandas as gpd
import numpy as np
from PIL import Image
import rasterio
from tqdm import tqdm

from src.data_processor import create_visualization_countinious_with_shapefiles


def process_raster_for_layout(
                            raster_path: Path,
                            list_for_background_layout: dict[str, list],
                            countries_shapefile: gpd.GeoDataFrame,
                            central_countries_shapefile: gpd.GeoDataFrame,
                            sea_shapefile: gpd.GeoDataFrame,
                            work_folder: Path,
                            palettes: dict
                            ) -> None:
    """
    Processes a raster file for visualization and classification, and organizes
    the resulting image into background layout categories.

    This function processes a given raster file by:
    1. Extracting its type from the file name.
    2. Reclassifying the raster if necessary.
    3. Creating a visualization of the raster with specified shapefiles as
        overlays.
    4. Categorizing the processed image into a background layout group based
        on its type.

    Args:
        raster_path (Path): The path to the raster file to be processed.
        list_for_background_layout (Dict[str, list]): A dictionary that
            organizes processed raster images into categories based on their
            type for layout purposes.
        countries_shapefile (gpd.GeoDataFrame): A GeoDataFrame containing the
            boundaries of countries.
        central_countries_shapefile (gpd.GeoDataFrame): A GeoDataFrame
            containing the boundaries of central countries.
        sea_shapefile (gpd.GeoDataFrame): A GeoDataFrame containing the
            boundaries of seas.
        work_folder (Path): The folder where processed files will be saved.

    Returns:
        None: The function does not return any value. It modifies
            `list_for_background_layout` in place.
    """
    # Extract the type of raster from the file name
    raster_parts_name = raster_path.stem.split("_")
    raster_type = raster_parts_name[0]

    # Choose palette based on raster type
    if raster_type not in palettes:
        raise ValueError(f"Palette for type {raster_type} not found")

    # Load the palette and boundaries for the given raster type
    palette = palettes[raster_type]
    boundaries = palette["boundaries"]
    colors = palette["colors"]
    classes = palette["classes"]
    continuous = palette["continuous_coloring"]

    # If raster type is not "AWP" or "FWI", reclassify it
    if raster_type not in ["AWP", "FWI"]:
        raster_path = reclassify_raster(raster_path, work_folder, boundaries)

    img_path = Path(work_folder) / Path(raster_path).name

    # Create visualization with shapefiles as overlays
    create_visualization_countinious_with_shapefiles(
                                raster_path, 
                                img_path, 
                                colors, 
                                classes, 
                                countries_shapefile,
                                central_countries_shapefile,
                                sea_shapefile,
                                continuous)

    # Determine the background type based on raster type
    if "AW" in raster_type:
        background_type = "_".join([raster_parts_name[0], raster_parts_name[1]])
        background_type = background_type[:-2]
    elif "FWI" in raster_type:
        background_type = "FWI_GenZ"
    else:
        background_type = raster_parts_name[0]

    if background_type not in list_for_background_layout:
        list_for_background_layout[background_type] = []

    # Append the image path to the appropriate background type category
    list_for_background_layout[background_type].append(img_path)


def reclassify_raster(
                    raster_path: Path, 
                    output_raster_path: Path, 
                    boundaries: list[float]
                    ) -> Path:
    """
    Reclassifies a raster based on specified boundaries and saves the output.

    This function reads an input raster, reclassifies its pixel values into 
    new classes based on the provided boundaries, and writes the reclassified
    raster to the specified output path. The new raster will have integer class
    values.

    Args:
        raster_path (Path): The path to the input raster file.
        output_raster_path (Path): The directory where the output raster file
            will be saved.
        boundaries (List[float]): A list of boundary values to define the
            reclassification bins.

    Returns:
        Path: The path to the saved reclassified raster file.
    """
    # Load the raster file
    with rasterio.open(raster_path) as src:
        raster_data = src.read(1)
        profile = src.profile
        # Default to -999 if NoData is not defined
        nodata_value = src.nodata if src.nodata is not None else -999.0
    
    # Reclassify the raster data based on the provided boundaries
    classes = np.digitize(raster_data, bins=boundaries, right=True) - 1
    
    
    final_path = Path(output_raster_path) / Path(raster_path).name

    # Update the profile with new data type and NoData value
    profile.update(dtype=rasterio.int16, count=1, nodata=nodata_value)

    # Write the reclassified raster to the output path
    with rasterio.open(final_path, 'w', **profile) as dst:
        dst.write(classes.astype(rasterio.int16), 1)

    return final_path


def rename_and_copy_images(
        list_for_background_layout: dict,
        src_root: str,
        dst_root: str) -> None:
    """
    Renames and copies image files based on date order into a target directory.

    Args:
        list_for_background_layout (dict): A dictionary where keys are indicator
            names and values are lists of file paths to be renamed and copied.
        src_root (str): The root directory containing the source image files.
        dst_root (str): The destination directory where renamed files will
            be copied.

    Returns:
        None: The function copies and renames files.
    """

    src_root = Path(src_root)
    dst_root = Path(dst_root)
    os.makedirs(dst_root, exist_ok=True)

    for indicator, paths in list_for_background_layout.items():
        # Sort files by date
        def extract_date(path):
            # Extract date from name
            stem = Path(path).stem
            date_part = stem.split("_")[-1]
            try:
                return datetime.strptime(date_part, "%Y-%m-%d")
            except ValueError:
                print(f"Skipping a file without a date: {path}")
                return datetime.min

        sorted_paths = sorted(paths, key=extract_date)

        # Copy with new names
        for i, src_path in enumerate(sorted_paths):
            src_path = Path(src_path)
            name_parts = src_path.stem.split("_")[:-1]

            for a, s in enumerate(name_parts):
                if s.startswith("DFM") and len(s) > 3:
                    name_parts[a] = "DFM_" + s[3:]

            new_name_png = "_".join(name_parts) + f"_{i}.png"
            dst_path_png = dst_root / new_name_png

            with Image.open(src_path) as img:

                rgb_img = img.convert("RGB")
                rgb_img.save(dst_path_png, "PNG", compress_level=4)
