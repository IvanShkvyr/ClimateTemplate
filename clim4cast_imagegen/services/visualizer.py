import matplotlib
matplotlib.use("Agg")

from concurrent.futures import ProcessPoolExecutor
from functools import partial
import logging
from multiprocessing import cpu_count
from pathlib import Path

import geopandas as gpd
from matplotlib.colors import (
    BoundaryNorm, ListedColormap, Normalize, LinearSegmentedColormap
    )
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from rasterio.plot import show
from tqdm import tqdm

from clim4cast_imagegen.core.config import AppConfig
from clim4cast_imagegen.core.constants import PALETTES_V1, PALETTES_V2
from clim4cast_imagegen.io.shp_io import load_visual_shapefiles, VisualLayers
from clim4cast_imagegen.io.raster_io import reclassify_raster, read_raster_for_visualization
from clim4cast_imagegen.services.raster_processor import (
                                            rename_and_copy_images,
                                            )

from clim4cast_imagegen.utils.palette_utils import PaletteConfig


def create_visualization_countinuous_with_shapefiles(
                                raster_file: str, 
                                final_path: str, 
                                colors_list: list[tuple], 
                                boundaries: list[float], 
                                countries_shapefile: gpd.GeoDataFrame, 
                                central_countries_shapefile: gpd.GeoDataFrame, 
                                sea_shapefile: gpd.GeoDataFrame,
                                continuous: bool = True
                                ) -> None:
    """
    Creates a visualization by overlaying raster data with shapefiles and
    saving the output as a PNG image. Works with both classified and continuous
    data.

    Args:
        raster_file (str): The path to the raster file to be visualized.
        final_path (str): The path where the output PNG image will be saved.
        colors_list (List[tuple]): A list of RGB colors to represent the data
            values at boundaries.
        boundaries (List[float]): A list of boundaries for color mapping. For
            continuous data, these define where each color in colors_list should
            be placed.
        countries_shapefile (gpd.GeoDataFrame): A GeoDataFrame representing the
            boundaries of countries.
        central_countries_shapefile (gpd.GeoDataFrame): A GeoDataFrame
            representing the boundaries of central countries.
        sea_shapefile (gpd.GeoDataFrame): A GeoDataFrame representing the
            boundaries of seas.
        continuous (bool, optional): If True, uses a continuous color gradient
            between boundaries. If False, uses discrete classes.

    Returns:
        None: The function saves the resulting plot to the specified
            `final_path` as a PNG image.
    """
    raster_data, transform, nodata_value, width, height = read_raster_for_visualization(raster_file)

    # Create a mask for NoData values and -999 values
    mask = (raster_data == -999)
    if nodata_value is not None:
        mask = np.logical_or(mask, raster_data == nodata_value)
    
    # Apply the mask
    masked_data = np.ma.masked_where(mask, raster_data)
    
    # Normalize colors to 0-1 range for matplotlib
    normalized_colors = [tuple(c / 255.0 for c in color) for color in colors_list]
    
    if continuous:
        # Create a mask for NoData values 
        no_data_mask = np.logical_or(raster_data == -999, raster_data == -1)
        
        # Calculate color positions based on boundaries 
        min_val = boundaries[1]  # First valid boundary after NoData
        max_val = boundaries[-1]
        positions = [(boundary - min_val) / (max_val - min_val) for boundary in boundaries[1:]]
        positions = [0] + positions  # Add 0 for the first color
        
        # Create a color map
        cmap = LinearSegmentedColormap.from_list("custom_cmap", 
                            list(zip(positions, normalized_colors[1:])))
        
        # Create a color map
        norm = Normalize(vmin=min_val, vmax=max_val)
        
        # Apply mask for NoData values
        masked_data = np.ma.masked_where(no_data_mask, raster_data)
    
    else:
        # For discrete classes, use the original approach
        cmap = ListedColormap(normalized_colors)
        norm = BoundaryNorm(boundaries, cmap.N, extend='max')

    # Create a figure for the visualization
    fig, ax = plt.subplots(figsize=(21, 21), dpi=300)

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
                dpi=300,
                bbox_inches='tight',
                pad_inches=-0.04
                )
    # Close the figure to free memory
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
        
    logger.info(f"Preparing single raster data for the website")
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
    Orchestrates visualization generation for all pallete variants.
    """
    # Load shapefiles
    shapefiles = load_visual_shapefiles(config, logger)
    logger.info(f"Loaded basic shapefiles")

    palette_configs = [
        PaletteConfig(
            name="normal",
            palettes=PALETTES_V1,
            temp_dir=config.folders.temp_img_v1,
            final_dir=config.folders.temp_final_v1,
        ),
        PaletteConfig(
            name="reduced",
            palettes=PALETTES_V2,
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
    
    """
    # Extract the type of raster from the file name
    raster_parts_name = raster_path.stem.split("_")
    raster_type = raster_parts_name[0]

    # Choose palette based on raster type
    if raster_type not in palettes:
        return None

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
    create_visualization_countinuous_with_shapefiles(
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

    return background_type, img_path
