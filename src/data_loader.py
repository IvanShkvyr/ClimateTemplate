from pathlib import Path

import geopandas as gpd
from pyproj import CRS
import rasterio
from rasterio.features import shapes
from rasterio.mask import mask
import yaml

from src.constants import CRS_FOR_DATA, PARAMETERS


def grab_files(
        directory_path: str,
        parameters: list = PARAMETERS,
        extensions: tuple = (".tif",)
        ) -> list:
    """TODO"""

    list_of_pathes = []

    directory_path = Path(directory_path)

    for element in directory_path.rglob("*"):

        if element.suffix.lower() not in extensions:
            continue

        name_of_file = element.stem

        
        for param in parameters:
            if param in name_of_file:
                list_of_pathes.append(element)
    
    return list_of_pathes


def load_config(file_path):
    """Завантажує конфігурацію з YAML файлу."""
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config


def load_data_from_mask_raster(frame_to_raster: str):
    """TODO"""
    # Читання меншого растра для отримання маски (без значень)
    with rasterio.open(frame_to_raster) as small_raster:
        small_raster_data = small_raster.read(1)  # Зчитуємо перший канал
        small_raster_transform = small_raster.transform  # Трансформація для геопросторого відображення

        # Створюємо маску на основі всіх пікселів (без фільтрації по значенням)
        mask_shapes = [
            geom for geom, value in shapes(small_raster_data, mask=None, transform=small_raster_transform)
        ]
    return mask_shapes


def load_shp(
        path_to_file: str,
        crs_mercator:CRS = CRS_FOR_DATA
        ) -> gpd.GeoDataFrame:
    """TODO"""

    shp_file = gpd.read_file(path_to_file)

    if shp_file.crs != crs_mercator:
        shp_file = shp_file.to_crs(crs_mercator)

    return shp_file



def read_and_clip_raster(path_to_raster: str, mask_shapes, output_path: str):
    """TODO"""
    # Читання великого растра
    with rasterio.open(path_to_raster) as large_raster:
        # Обрізаємо велике зображення по геометрії маски
        large_raster_data, large_raster_transform = mask(large_raster, mask_shapes, crop=True)

        # Створення нового метаданих для збереження правильної геопросторової прив'язки
        output_meta = large_raster.meta.copy()
        output_meta.update({
            'driver': 'GTiff',
            'count': large_raster.count,
            'dtype': large_raster.dtypes[0],
            'width': large_raster_data.shape[2],
            'height': large_raster_data.shape[1],
            'transform': large_raster_transform  # Зберігаємо правильну трансформацію
        })

        # Збереження обрізаного зображення з правильною трансформацією
        with rasterio.open(output_path, 'w', **output_meta) as dst:
            dst.write(large_raster_data)


