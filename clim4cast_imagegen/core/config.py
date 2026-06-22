import os
import yaml
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv


DEFAULT_CONFIG_FILE = "config.yaml"


@dataclass
class FolderPaths:
    temp: Path
    temp_crop: Path
    temp_trans: Path
    temp_rec: Path
    temp_img_v1: Path
    temp_img_v2: Path
    temp_final_v1: Path
    temp_final_v2: Path
    temp_downloads: Path
    to_send: Path


@dataclass
class ShapefilePaths:
    countries: Path
    central_countries: Path
    sea: Path


@dataclass
class Clim4CastConfig:
    username: str
    password: str
    base_url: str


@dataclass
class AppConfig:
    folders: FolderPaths
    shapes: ShapefilePaths
    api: Clim4CastConfig
    source_path: Path
    templates_path: Path
    frame_raster: Path
    font_path: Path


def load_app_config(config_path: str = DEFAULT_CONFIG_FILE) -> AppConfig:
    """
    Load application configuration, merging YAML and Environment variables
    """
    load_dotenv()

    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    f_cfg = cfg["folders_paths"]
    s_cfg = cfg["shapefiles_paths"]

    username = os.getenv("API_USERNAME")
    password = os.getenv("API_PASSWORD", "")

    if not username:
        raise ValueError("Critical error: API_USERNAME not found in .env file!")

    return AppConfig(
        folders=FolderPaths(
            temp=Path(f_cfg["temp_folder"]),
            temp_crop=Path(f_cfg["temp_folder_crop"]),
            temp_trans=Path(f_cfg["temp_folder_trans"]),
            temp_rec=Path(f_cfg["temp_folder_rec"]),
            temp_img_v1=Path(f_cfg["temp_folder_img_v1"]),
            temp_img_v2=Path(f_cfg["temp_folder_img_v2"]),
            temp_final_v1=Path(f_cfg["temp_final_img_v1"]),
            temp_final_v2=Path(f_cfg["temp_final_img_v2"]),
            temp_downloads=Path(f_cfg["temp_folder_final"]),
            to_send=Path(f_cfg["folder_to_send"])
        ),
        shapes=ShapefilePaths(
            countries=Path(s_cfg["path_countries"]),
            central_countries=Path(s_cfg["path_central_countries"]),
            sea=Path(s_cfg["path_sea"])
        ),
        api=Clim4CastConfig(
            base_url=cfg["clim4cast"]["base_url"],
            username=username,
            password=password
        ),
        source_path=Path(cfg["path_to_source"]),
        templates_path=Path(cfg["path_to_tamplates"]),
        frame_raster=Path(cfg["frame_to_raster"]),
        font_path=Path(cfg["font_path"])
    )
