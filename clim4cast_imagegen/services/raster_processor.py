import logging
from pathlib import Path

from tqdm import tqdm

from clim4cast_imagegen.core.config import AppConfig
from clim4cast_imagegen.core.constants import CRS_FOR_DATA
from clim4cast_imagegen.io.local_storage import grab_files, ensure_dir
from clim4cast_imagegen.io.raster_io import (
                                read_and_clip_raster,
                                load_data_from_mask_raster,
                                convert_coordinate_system_in_raster
                                )
from clim4cast_imagegen.services.layout_engine import process_image
from clim4cast_imagegen.utils.pathname_utils import build_new_filename, extract_date




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


def rename_and_copy_images(
        files_map: dict,
        dst_root: Path,
        logger: logging.Logger,
        ) -> None:
    """
    Sorts images by date, renames them, and saves to destination directory.
    """

    dst_root = Path(dst_root)
    ensure_dir(dst_root)

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
