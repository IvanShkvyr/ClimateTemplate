import logging
from pathlib import Path

import numpy as np
from pyproj import CRS
import rasterio
from rasterio.warp import reproject, Resampling, calculate_default_transform
from tqdm import tqdm

from clim4cast_imagegen.core.config import AppConfig
from clim4cast_imagegen.core.constants import CRS_FOR_DATA
from clim4cast_imagegen.io.local_storage import grab_files
from clim4cast_imagegen.io.raster_io import (
                                read_and_clip_raster,
                                load_data_from_mask_raster
                                )
from clim4cast_imagegen.services.layout_engine import process_image
from clim4cast_imagegen.utils.pathname_utils import build_new_filename, extract_date


def convert_coordinate_system_in_raster(
                                        target_crs: CRS,
                                        input_path: Path,
                                        output_path: Path
                                        ) -> None:
    """
    Converts the coordinate system of the input raster to the specified CRS 
    and saves the reprojected raster to the given output path.

    Args:
        crs_mercator (CRS): The target coordinate reference system (CRS) to
            which the raster should be converted. Typically, this would be the
            Web Mercator projection (EPSG:3857).
        input_path (str): The file path of the input raster that needs to be
            reprojected.
        output_path (str): The file path where the reprojected raster will
            be saved.

    Returns:
        None: The function performs the reprojecting and saves the resulting
            raster to the specified output path.
    """
    # Open the source raster to check its CRS and other properties
    with rasterio.open(input_path) as src:

        # Check if the CRS of the raster is different from the target CRS
        if src.crs != target_crs:
            # Calculate the transformation needed to convert the current CRS
            # to target CRS
            transform, width, height = calculate_default_transform(
                src.crs, target_crs, src.width, src.height, *src.bounds
            )
            nodata_value = src.nodata

            # Open a new raster file for saving the reprojected data
            with rasterio.open(output_path, "w", driver="GTiff",
                            count=1, dtype=src.dtypes[0],
                            crs=target_crs, transform=transform,
                            width=width, height=height,
                            nodata=nodata_value) as dst:
                
                # Reproject the data from the source CRS to the target CRS
                reproject(
                    source=rasterio.band(src, 1),
                    destination=rasterio.band(dst, 1),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=target_crs,
                    resampling=Resampling.nearest
                )


def generate_base_raster(
        path_to_data: Path,
        config: AppConfig,
        logger: logging.Logger,
        ) -> list:
    """
    Generate base raster images from source data.
    """
    # Create file lists
    list_of_rasters = list(grab_files(path_to_data))
    logger.info(f"Found {len(list_of_rasters)} source files.")

    # Create mask shape
    frame_to_raster = config.frame_raster
    mask_shape = load_data_from_mask_raster(frame_to_raster, logger)

    logger.info(f"Start process rasters")
    list_of_img = process_rasters(
        list_of_rasters,
        mask_shape,
        config.folders.temp_crop,
        config.folders.temp_trans,
        )
    logger.info(f"All base rasters were clipped, converted, and saved "
                f"to {config.folders.temp_crop}")
    
    return list_of_img


def process_rasters(
                    list_of_rasters: list[Path],
                    mask_shape: dict,
                    temp_folder: Path,
                    temp_folder_img: Path,
                    ) -> list[Path]:
    """
    Processes rasters by clipping them with a mask and converting their
    coordinate system.

    This function iterates through a list of raster files, clips each raster
    using a provided mask shape, and converts the coordinate system to a
    specified one. The processed rasters are saved in the specified temporary
    folders.

    Args:
        list_of_rasters (List[Path]): A list of raster file paths to be
            processed.
        mask_shape (dict): The shape used for clipping the rasters.
        tump_folder (Path): The temporary folder path where clipped rasters
            will be saved.
        tump_folder_img (Path): The temporary folder path where coordinate
            system converted rasters will be saved.

    Returns:
        List[Path]: A list of file paths for the processed rasters (with the
            converted coordinate system).
    """
    list_of_img = []
    for raster in tqdm(list_of_rasters):
        # Define output paths for clipped raster and coordinate system converted
        # raster
        output_path = temp_folder / raster.name
        output_path_2 = temp_folder_img / raster.name
        # Clip raster based on the mask shape and save the result
        read_and_clip_raster(raster, mask_shape, output_path)
        # Convert the coordinate system of the raster and save the result
        convert_coordinate_system_in_raster(
                                            CRS_FOR_DATA,
                                            output_path,
                                            output_path_2
                                            )
         # Append the processed raster to the list
        list_of_img.append(output_path_2)

    return list_of_img


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
        files_map: dict,
        dst_root: Path,
        logger: logging.Logger,
        ) -> None:
    """
    Sorts images by date, renames them, and saves to destination directory.
    """

    dst_root = Path(dst_root)
    dst_root.mkdir(parents=True, exist_ok=True)

    for paths in files_map.values():
        path_objs = [Path(p) for p in paths]
        sorted_paths = sorted(
            path_objs,
            key=lambda p: extract_date(p, logger)
        )

        # Copy with new names
        for i, src_path in enumerate(sorted_paths):
            new_name = build_new_filename(src_path, i)
            dst_path = dst_root / new_name

            process_image(src_path, dst_path, logger)
