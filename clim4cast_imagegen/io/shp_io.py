import logging
from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd
from pyproj import CRS

from clim4cast_imagegen.core.config import AppConfig
from clim4cast_imagegen.core.constants import CRS_FOR_DATA


@dataclass
class VisualLayers:
    """Container for loaded shape files"""
    countries: gpd.GeoDataFrame
    central: gpd.GeoDataFrame
    sea: gpd.GeoDataFrame


def load_visual_shapefiles(
        config: AppConfig, logger: logging.Logger
        ) -> VisualLayers:
    """
    Orchestrates loading of all necessary vector layers
    """
    return VisualLayers(
    countries=load_shp(config.shapes.countries, logger),
    central=load_shp(config.shapes.central_countries, logger),
    sea=load_shp(config.shapes.sea, logger),
    )


def load_shp(
        path: Path,
        logger: logging.Logger,
        target_crs: CRS = CRS_FOR_DATA,
        ) -> gpd.GeoDataFrame:
    """
    Loads a shapefile into a GeoDataFrame and transforms it to a specified CRS
    if needed.
    """
    if not path.exists():
        logger.error(f"Shapefile missing: {path}")
        raise FileNotFoundError(f"Could not find shapefile at {path}")
    
    try:
        # Read the shapefile into a GeoDataFrame
        shp_file = gpd.read_file(path)

        if shp_file.crs is None or not shp_file.crs.equals(target_crs):
            logger.debug(f"Reprojecting {path.name} to {target_crs.to_epsg()}")
            shp_file = shp_file.to_crs(target_crs)
        
        return shp_file
    except Exception as err:
        logger.exception(f"Failed to load shapefile {path.name}: {err}")
        raise
