import matplotlib

matplotlib.use("Agg")

import logging
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from multiprocessing import cpu_count
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import (
    BoundaryNorm,
    LinearSegmentedColormap,
    ListedColormap,
    Normalize,
)
from rasterio.plot import show
from tqdm import tqdm

from clim4cast_imagegen.core.config import AppConfig
from clim4cast_imagegen.core.constants import DPI
from clim4cast_imagegen.core.palette_types import (
    PALETTE_REGISTRY_V1,
    PALETTE_REGISTRY_V2,
)
from clim4cast_imagegen.io.image_io import trim_image_sides
from clim4cast_imagegen.io.raster_io import (
    read_raster_for_visualization,
    reclassify_raster,
)
from clim4cast_imagegen.io.shp_io import VisualLayers, load_visual_shapefiles
from clim4cast_imagegen.services.raster_processor import (
    rename_and_copy_images,
)
from clim4cast_imagegen.utils.palette_utils import PaletteConfig
from clim4cast_imagegen.utils.pathname_utils import background_type_from_raster


def create_map_visualization(
                                raster_file: str,
                                final_path: str,
                                colors: list[tuple],
                                boundaries: list[float],
                                countries_shapefile: gpd.GeoDataFrame,
                                central_countries_shapefile: gpd.GeoDataFrame,
                                sea_shapefile: gpd.GeoDataFrame,
                                continuous: bool = True
                                ) -> None:
    """Render a raster as a PNG map with country and sea layers on top."""
    raster_data, transform, nodata_value, width, height = (
        read_raster_for_visualization(raster_file)
    )

    # Create a mask for NoData values and -999 values
    mask = (raster_data == -999)
    if nodata_value is not None:
        mask = np.logical_or(mask, raster_data == nodata_value)

    # Apply the mask
    masked_data = np.ma.masked_where(mask, raster_data)

    # Normalize colors to 0-1 range for matplotlib
    normalized_colors = [
        tuple(c / 255.0 for c in color) for color in colors
        ]

    if continuous:
        # Create a mask for NoData values
        no_data_mask = np.logical_or(raster_data == -999, raster_data == -1)

        # Calculate color positions based on boundaries
        min_val = boundaries[1]  # First valid boundary after NoData
        max_val = boundaries[-1]
        positions = [
            (boundary - min_val) / (max_val - min_val)
            for boundary in boundaries[1:]
            ]
        positions = [0] + positions  # Add 0 for the first color

        # Create a color map
        cmap = LinearSegmentedColormap.from_list("custom_cmap",
                    list(zip(positions, normalized_colors[1:], strict=True)))

        # Create a normalizer for the value range
        norm = Normalize(vmin=min_val, vmax=max_val)

        # Apply mask for NoData values
        masked_data = np.ma.masked_where(no_data_mask, raster_data)

    else:
        # For discrete classes, use the original approach
        cmap = ListedColormap(normalized_colors)
        norm = BoundaryNorm(boundaries, cmap.N, extend='max')

    # Create a figure for the visualization
    fig, ax = plt.subplots(figsize=(21, 21), dpi=DPI)

    try:

        # Set the extent of the plot based on the raster transform
        ax.set_xlim([transform[2], transform[2] + width * transform[0]])
        ax.set_ylim([transform[5] + height * transform[4], transform[5]])

        # Show the raster data with the colormap and normalization
        show(masked_data, ax=ax, cmap=cmap, norm=norm, transform=transform)

        # Overlay the shapefiles on the plot
        sea_shapefile.plot(
                        ax=ax,
                        facecolor=(156/255, 156/255, 156/255),
                        edgecolor='none',
                        linewidth=3
                        )
        countries_shapefile.plot(
                                ax=ax,
                                facecolor='none',
                                edgecolor='black',
                                linewidth=1.2
                                )
        central_countries_shapefile.plot(
                                        ax=ax,
                                        facecolor='none',
                                        edgecolor='black',
                                        linewidth=3.2
                                        )

        ax.set_axis_off()

        # Save the final visualization as a PNG image
        plt.savefig(
                    final_path,
                    format='png',
                    dpi=DPI,
                    bbox_inches='tight',
                    pad_inches=-0.04
                    )

        trim_image_sides(Path(final_path), left=15, bottom=15)

    finally:
        plt.close(fig)


def generate_palette_images(
        rasters: list,
        palette_cfg: PaletteConfig,
        shapefiles: VisualLayers,
        logger: logging.Logger
    ) -> dict:
    """
    Generate visualization images for a single palette variant.
    """
    logger.info(f"Start visualization for palette: {palette_cfg.name}")
    layout_index = {}

    worker_func = partial(
        process_single_raster,
        countries_shapefile=shapefiles.countries,
        central_countries_shapefile=shapefiles.central,
        sea_shapefile=shapefiles.sea,
        work_folder=palette_cfg.temp_dir,
        palettes=palette_cfg.palettes
    )

    max_workers = min(cpu_count() - 1 if cpu_count() > 1 else 1, 8)

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        results = list(tqdm(
                            executor.map(worker_func, rasters),
                            total=len(rasters),
                            desc=palette_cfg.name)
                            )

    # Collect the results from all processes into the final dictionary
    for res in results:
        if res:
            bg_type, path = res
            if bg_type not in layout_index:
                layout_index[bg_type] = []
            layout_index[bg_type].append(path)

    logger.info("Preparing single raster data for the website")
    rename_and_copy_images(
        files_map=layout_index,
        dst_root=palette_cfg.final_dir,
        logger=logger,
    )

    return layout_index


def generate_visualizations(
                            config: AppConfig,
                            rasters: list,
                            logger: logging.Logger
                            ) -> dict:
    """
    Orchestrate visualization generation for all palette variants.
    """
    shapefiles = load_visual_shapefiles(config, logger)
    logger.info("Loaded basic shapefiles")

    palette_configs = [
        PaletteConfig(
            name="normal",
            palettes=PALETTE_REGISTRY_V1,
            temp_dir=config.folders.temp_img_v1,
            final_dir=config.folders.temp_final_v1,
        ),
        PaletteConfig(
            name="reduced",
            palettes=PALETTE_REGISTRY_V2,
            temp_dir=config.folders.temp_img_v2,
            final_dir=config.folders.temp_final_v2,
        ),
    ]

    visualization_results = {}

    for palette_cfg in palette_configs:
        visualization_results[palette_cfg.name] = generate_palette_images(
            rasters=rasters,
            palette_cfg=palette_cfg,
            shapefiles=shapefiles,
            logger=logger,
        )

    return visualization_results


def process_single_raster(
        raster_path: Path,
        countries_shapefile: gpd.GeoDataFrame,
        central_countries_shapefile: gpd.GeoDataFrame,
        sea_shapefile: gpd.GeoDataFrame,
        work_folder: Path,
        palettes: dict
        ):
    """
    Render one raster to PNG and return its background type and image path.
    """
    # Extract the type of raster from the file name
    raster_name_parts = raster_path.stem.split("_")

    # Choose palette based on raster type
    if raster_name_parts[0] not in palettes:
        return None

    # Load the palette and boundaries for the given raster type
    palette = palettes[raster_name_parts[0]]
    boundaries = palette.boundaries
    colors = palette.colors
    classes = palette.classes
    continuous = palette.continuous_coloring

    if palette.reclassify:
        raster_path = reclassify_raster(raster_path, work_folder, boundaries)

    img_path = Path(work_folder) / Path(raster_path).name

    # Create visualization with shapefiles as overlays
    create_map_visualization(
                                raster_path,
                                img_path,
                                colors,
                                classes,
                                countries_shapefile,
                                central_countries_shapefile,
                                sea_shapefile,
                                continuous)

    background_type = background_type_from_raster(raster_name_parts)

    return background_type, img_path
