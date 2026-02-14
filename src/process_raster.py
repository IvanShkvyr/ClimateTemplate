from pathlib import Path

from pyproj import CRS
import rasterio
from rasterio.warp import reproject, Resampling, calculate_default_transform
from tqdm import tqdm

from src.constants import CRS_FOR_DATA
from src.data_loader import read_and_clip_raster



def convert_coordinate_systen_in_raster(
                                        target_crs: CRS,
                                        input_path: str,
                                        output_path: str
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

            # # Print a success message once the raster is reprojected and saved
            # print(f"Raster reprojected and saved to {output_path}")



def process_rasters(
                    list_of_rasters: list[Path],
                    mask_shape: dict,
                    tump_folder: Path,
                    tump_folder_img: Path,
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
        output_path = tump_folder / raster.name
        output_path_2 = tump_folder_img / raster.name
        # Clip raster based on the mask shape and save the result
        read_and_clip_raster(raster, mask_shape, output_path)
        # Convert the coordinate system of the raster and save the result
        convert_coordinate_systen_in_raster(
                                            CRS_FOR_DATA,
                                            output_path,
                                            output_path_2
                                            )
         # Append the processed raster to the list
        list_of_img.append(output_path_2)

    return list_of_img
