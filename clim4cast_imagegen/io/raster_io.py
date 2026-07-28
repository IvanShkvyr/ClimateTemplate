import logging
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from pyproj import CRS
from rasterio.features import shapes
from rasterio.mask import mask
from rasterio.warp import Resampling, calculate_default_transform, reproject


def load_mask_shapes(
        frame_to_raster: Path, logger: logging.Logger,
        ) -> list[Any]:
    """
    Load mask shapes from a raster file.
    """
    if not frame_to_raster.exists():
        logger.error(f"Mask raster not found: {frame_to_raster}")
        raise FileNotFoundError(f"Missing mask file: {frame_to_raster}")

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
    Clip a raster with the given shapes and save it.
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



def convert_coordinate_system_in_raster(
                                        target_crs: CRS,
                                        input_path: Path,
                                        output_path: Path
                                        ) -> None:
    """Reproject a raster to the given CRS and save it."""
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


def reclassify_raster(
                    raster_path: Path,
                    output_raster_path: Path,
                    boundaries: list[float]
                    ) -> Path:
    """Convert raster values into class indices and save them as int16."""
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


def read_raster_for_visualization(
        raster_path: Path
        ) -> tuple[np.ndarray, rasterio.Affine, float|None, int, int]:
    """
    Read raster data and metadata required for visualization.
    """
    with rasterio.open(raster_path) as src:
        return src.read(1), src.transform, src.nodata, src.width, src.height
