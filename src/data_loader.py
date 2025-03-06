from datetime import date
from pathlib import Path
import shutil

import geopandas as gpd
from pyproj import CRS
import rasterio
from rasterio.features import shapes
from rasterio.mask import mask
import yaml

from src.constants import CRS_FOR_DATA, PARAMETERS


def create_data_folder_path(main_path: str, today: date) -> str:
    """
    Create a path to a folder based on the current date.

    This function takes the main path as input and appends the current date
    in the format 'YYYY-MM-DD' to it, creating a final path for the data folder.
    
    Args:
        main_path (str): The base directory path where the data folder will be
            created.
        today (date): The specific date used to generate the folder path, in
            'YYYY-MM-DD' format.

    Returns:
        str: The complete path to the data folder with the current date appended
    """
    year = today.strftime("%Y")
    day = today.strftime("%Y-%m-%d")

    # Combine the main path with the current date
    final_path = main_path + "/" + year + "/" + day

    return final_path


def grab_files(
                directory_path: str,
                parameters: dict = PARAMETERS,
                extensions: tuple = (".tif",)
                ) -> list:
    """
    Searches a given directory and its subdirectories for files with specific
    extensions and names that match any of the parameters in the provided
    dictionary.

    Args:
        directory_path (str): The directory path where the search will begin.
        parameters (dict): A dictionary containing parameters that should be
            present in the file name (default is PARAMETERS).
        extensions (tuple): A tuple containing file extensions to search for
            (default is (".tif",)).

    Returns:
        list: A list of Path objects pointing to files that match the given
            criteria.
    """
    # Initialize an empty list to store the paths of matching files
    list_of_pathes = []

    directory_path = Path(directory_path)

    # Loop through all elements in the directory and its subdirectories
    for element in directory_path.rglob("*"):
        # Skip files that don't match the desired extensions
        if element.suffix.lower() not in extensions:
            continue

        name_of_file = element.stem

        # Check if any of the parameters are present in the file name
        for param in parameters:
            if param in name_of_file:
                list_of_pathes.append(element)

    # Return the list of matching file paths
    return list_of_pathes


def load_config(file_path: str) -> dict:
    """
    Loads configuration data from a YAML file.

    Args:
        file_path (str): The path to the YAML configuration file.

    Returns:
        dict: A dictionary containing the parsed configuration data from
            the YAML file.
    """
    # Open the YAML file in read mode
    with open(file_path, "r") as file:
        config = yaml.safe_load(file)

    return config


def load_data_from_mask_raster(frame_to_raster: str) -> list:
    """
    Loads data from a raster file to create a mask based on the raster values.

    Args:
        frame_to_raster (str): The path to the raster file that will be used to
            create the mask.

    Returns:
        list: A list of geometries (shapes) representing the mask created from
            the raster data.
    """
    # Open the raster file using rasterio to read its data
    with rasterio.open(frame_to_raster) as small_raster:
        # Read the first band (channel) of the raster file into a numpy array
        small_raster_data = small_raster.read(1)
        small_raster_transform = (
            small_raster.transform
        )

        # Create mask shapes from the raster data using the 'shapes' function
        # This converts raster values into geometries (polygons) based on raster
        mask_shapes = [
            geom
            for geom, value in shapes(
                small_raster_data, mask=None, transform=small_raster_transform
            )
        ]

    return mask_shapes


def load_shp(
        path_to_file: str,
        target_crs: CRS = CRS_FOR_DATA
        ) -> gpd.GeoDataFrame:
    """
    Loads a shapefile into a GeoDataFrame and transforms it to a specified CRS
    if needed.

    Args:
        path_to_file (str): The path to the shapefile to be loaded.
        target_crs (CRS, optional): The desired coordinate reference system
            (CRS) to transform the shapefile to. Default is `CRS_FOR_DATA`.

    Returns:
        gpd.GeoDataFrame: A GeoDataFrame containing the shapefile data,
            transformed to the target CRS if necessary.
    """
    # Read the shapefile into a GeoDataFrame
    shp_file = gpd.read_file(path_to_file)

    # Check if the CRS of the shapefile is different from the target CRS
    if shp_file.crs != target_crs:
        shp_file = shp_file.to_crs(target_crs)

    return shp_file


def read_and_clip_raster(
        path_to_raster: str,
        mask_shapes,
        output_path: str
        ) -> None:
    """
    Reads a large raster file, clips it using the provided mask shapes, 
    and saves the clipped raster to the specified output path.

    Args:
        path_to_raster (str): The file path to the large raster to be read and
            clipped.
        mask_shapes (list): A list of geometries (shapes) used to clip the
            raster.
        output_path (str): The file path where the clipped raster will be saved.

    Returns:
        None: The function saves the clipped raster to the specified output path
    """
    # Read the large raster file
    with rasterio.open(path_to_raster) as large_raster:
        # Clip the raster using the provided mask shapes (crop=True ensures that
        # the raster is cropped to the mask area)
        large_raster_data, large_raster_transform = mask(
            large_raster, mask_shapes, crop=True
        )

        # Create new metadata for the output raster to ensure the correct
        # geospatial referencing
        output_meta = large_raster.meta.copy()
        output_meta.update(
            {
                "driver": "GTiff",
                "count": large_raster.count,
                "dtype": large_raster.dtypes[0],
                "width": large_raster_data.shape[2],
                "height": large_raster_data.shape[1],
                "transform": large_raster_transform,
            }
        )

        # Write the clipped raster data to the output file
        with rasterio.open(output_path, "w", **output_meta) as dst:
            dst.write(large_raster_data)


def remove_local_directory(temp_path: str) -> None:
    """
    Removes the specified directory.

    Parameters:
        temp_path (str): Path to the directory to be removed.

    Returns:
        None
    """
    temp_folder = Path(temp_path)

    # Check if the directory exists and is indeed a directory
    if temp_folder.exists() and temp_folder.is_dir():
        shutil.rmtree(temp_folder)
