from dataclasses import dataclass
import logging

from pathlib import Path
import os
from tqdm import tqdm

from src.data_loader import load_visual_shapefiles
from src.constants import PALETTES_V1, PALETTES_V2
from src.raster_utils import process_raster_for_layout, rename_and_copy_images





@dataclass(frozen=True)
class PaletteConfig:
    name: str
    palettes: dict
    temp_dir: Path
    final_dir: Path


def select_palette(target_folder: Path, visualizations: dict):
    """
    Select visualization layout based on target folder structure.
    """
    parent_name = target_folder.parent.name

    if parent_name not in visualizations:
        raise ValueError(f"Unknown palette folder: {parent_name}")

    return visualizations[parent_name]


def generate_palette_images(
        rasters: list,
        palette_cfg: PaletteConfig,
        shapefiles: dict,
        logger: logging.Logger
    ) -> dict:
    """
    Generate visualization images for a singl palette variant.
    """
    logger.info(f"Start visualization for palette: {palette_cfg.name}")

    layout_index = {}

    for raster_path in tqdm(rasters, desc=palette_cfg.name):
        process_raster_for_layout(
            raster_path=raster_path,
            list_for_background_layout=layout_index,
            countries_shapefile=shapefiles["countries"],
            central_countries_shapefile=shapefiles["central"],
            sea_shapefile=shapefiles["sea"],
            work_folder=palette_cfg.temp_dir,
            palettes=palette_cfg.palettes,
            )
        
    logger.info(f"копіювання і перейменування для сайту")

    rename_and_copy_images(
        list_for_background_layout=layout_index,
        src_root=palette_cfg.temp_dir,
        dst_root=palette_cfg.final_dir,
        )

    logger.info(f"Finished palette: {palette_cfg.name}")

    return layout_index


def generate_visualizations(
                            config: dict,
                            rasters: list,
                            directories: dict,
                            logger: logging.Logger
                            ) -> dict:
    """
    Orchestrates visualization generation for all pallete variants.
    """
    # Load shapefiles
    shapefiles = load_visual_shapefiles(config)
    logger.info(f"Loaded basic shapefiles")

    palette_configs = [
        PaletteConfig(
            name="normal",
            palettes=PALETTES_V1,
            temp_dir=directories["normal_data"],
            final_dir=directories["final_normal"]
        ),
        PaletteConfig(
            name="reduced",
            palettes=PALETTES_V2,
            temp_dir=directories["reduced_data"],
            final_dir=directories["final_reduced"]
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
