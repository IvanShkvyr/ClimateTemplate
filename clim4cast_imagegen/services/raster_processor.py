import logging
from pathlib import Path
from typing import Any

from tqdm import tqdm

from clim4cast_imagegen.core.config import AppConfig
from clim4cast_imagegen.core.constants import CRS_FOR_DATA
from clim4cast_imagegen.io.local_storage import ensure_dir, iter_matching_files
from clim4cast_imagegen.io.raster_io import (
    convert_coordinate_system_in_raster,
    load_mask_shapes,
    read_and_clip_raster,
)
from clim4cast_imagegen.services.layout_engine import convert_to_rgb_png
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
    rasters = list(iter_matching_files (path_to_data))
    logger.info(f"Found {len(rasters)} source files.")

    # Create mask shape
    frame_to_raster = config.frame_raster
    mask_shape = load_mask_shapes(frame_to_raster, logger)

    logger.info("Start process rasters")
    images = process_rasters(
        rasters,
        mask_shape,
        config.folders.temp_crop,
        config.folders.temp_trans,
        )
    logger.info(f"All base rasters were clipped, converted, and saved "
                f"to {config.folders.temp_crop}")

    return images


def process_rasters(
                    rasters: list[Path],
                    mask_shape: list[Any],
                    temp_folder: Path,
                    temp_folder_img: Path,
                    ) -> list[Path]:
    """Clip rasters with the frame mask and reproject them to the target CRS."""
    images = []
    for raster in tqdm(rasters):
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

        images.append(output_path_2)

    return images


def rename_and_copy_images(
        files_map: dict,
        dst_root: Path,
        logger: logging.Logger,
        ) -> None:
    """
    Sort images by date, rename them, and copy them to the destination.
    """

    dst_root = Path(dst_root)
    ensure_dir(dst_root)

    for paths in files_map.values():
        path_objs = [Path(p) for p in paths]
        sorted_paths = sorted(
            path_objs,
            key=extract_date
        )

        # Copy with new names
        for i, src_path in enumerate(sorted_paths):
            new_name = build_new_filename(src_path, i)
            dst_path = dst_root / new_name

            convert_to_rgb_png(src_path, dst_path, logger)
