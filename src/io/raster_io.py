import logging
from pathlib import Path
from typing import Any

import rasterio
from rasterio.features import shapes
from rasterio.mask import mask


def load_data_from_mask_raster(
        frame_to_raster: Path, logger: logging.Logger,
        ) -> list[Any]:
    """
    Loads data from a raster file to create a mask based on the raster values.

    Returns:
        list: A list of geometries (shapes) representing the mask created from
        the raster data.
    """
    if not frame_to_raster.exists():
        logger.error(f"Mask raster not found: {frame_to_raster}")
        raise FileNotFoundError(f"Missing mask file: {frame_to_raster}")

    # Open the raster file using rasterio to read its data
    with rasterio.open(frame_to_raster) as src:
        # Read the first band (channel) of the raster file into a numpy array
        src_data = src.read(1)
        src_transform = (
            src.transform
        )

        # Create mask shapes from the raster data using the 'shapes' function
        # This converts raster values into geometries (polygons) based on raster
        mask_shapes = [
            geom
            for geom, value in shapes(
                src_data, mask=None, transform=src_transform
            )
        ]

    return mask_shapes


def read_and_clip_raster(
        path_to_raster: Path,
        mask_shapes: list[Any],
        output_path: Path,
        ) -> None:
    """
    Clips a raster using provided shapes and saves it with updated metadata.

    Returns:
        None: The function saves the clipped raster to the specified output path
    """
    # Read the large raster file
    with rasterio.open(path_to_raster) as src:
        # Clip the raster using the provided mask shapes (crop=True ensures that
        # the raster is cropped to the mask area)
        src_data, src_transform = mask(src, mask_shapes, crop=True)

        # Create new metadata for the output raster to ensure the correct
        # geospatial referencing
        output_meta = src.meta.copy()
        output_meta.update(
            {
                "driver": "GTiff",
                "count": src.count,
                "dtype": src.dtypes[0],
                "width": src_data.shape[2],
                "height": src_data.shape[1],
                "transform": src_transform,
                "compress": "lzw"
            }
        )

        # Write the clipped raster data to the output file
        with rasterio.open(output_path, "w", **output_meta) as dst:
            dst.write(src_data)
