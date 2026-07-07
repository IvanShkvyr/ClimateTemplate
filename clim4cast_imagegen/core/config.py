import os
import yaml
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv
from typing import Dict, List


PROJECT_ROOT = Path(
    os.getenv("APP_ROOT", Path(__file__).resolve().parent.parent.parent)
    )
DEFAULT_CONFIG_FILE = "config.yaml"
DEFAULT_CONFIG_PATH = PROJECT_ROOT / DEFAULT_CONFIG_FILE

REQUIRED_PATH_KEYS = [
    "temp_folder",
    "temp_folder_crop",
    "temp_folder_trans",
    "temp_folder_rec",
    "temp_folder_img_v1",
    "temp_folder_img_v2",
    "temp_final_img_v1",
    "temp_final_img_v2",
    "temp_folder_final",
    "folder_to_send",
]

REQUIRED_SHP_KEYS = [
    "path_countries",
    "path_central_countries",
    "path_sea",
]

REQUIRED_FILE_KEYS = [
    "path_to_source",
    "path_to_tamplates",
    "frame_to_raster",
    "font_path"
    ]


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
    dry_run: bool = True


def _require_keys(d: Dict, section_name: str, keys: List[str]) -> None:
    """
    Validate that all required keys exist in a configuration section
    """
    missing_keys = []

    if section_name not in d:
        raise ValueError(f"Missing configuration section: \'{section_name}\'")
    
    for key in keys:
        if key not in d[section_name]:
            missing_keys.append(key)

    if missing_keys:
        raise ValueError(
            f"Missing required keys in section '{section_name}': "
            f"{', '.join(missing_keys)}"
        )


def _validate_structure(d: Dict) -> None:
    """
    Validate the structure of the configuration dictionary.
    """
    _require_keys(d, "folders_paths", REQUIRED_PATH_KEYS)
    _require_keys(d, "shapefiles_paths", REQUIRED_SHP_KEYS)
    _require_keys(d, "clim4cast", ["base_url"])

    missing_keys = [key for key in REQUIRED_FILE_KEYS if key not in d]

    if missing_keys:
        raise ValueError(
            f"Missing required keys: "
            f"{', '.join(missing_keys)}"
        )


def _build_app_config(cfg: Dict) -> AppConfig:
    """
    Build an AppConfig instance from a validated configuration dictionary
    """
    f_cfg = cfg["folders_paths"]
    s_cfg = cfg["shapefiles_paths"]

    username = os.getenv("API_USERNAME")
    password = os.getenv("API_PASSWORD", "")
    raw = os.getenv("CLIM4CAST_DRY_RUN", "true").strip().lower()
    dry_run = raw not in ("false", "0", "no")

    if not username:
        raise ValueError("Critical error: API_USERNAME not found in .env file!")

    return AppConfig(
        folders=FolderPaths(
            temp=PROJECT_ROOT / Path(f_cfg["temp_folder"]),
            temp_crop=PROJECT_ROOT / Path(f_cfg["temp_folder_crop"]),
            temp_trans=PROJECT_ROOT / Path(f_cfg["temp_folder_trans"]),
            temp_rec=PROJECT_ROOT / Path(f_cfg["temp_folder_rec"]),
            temp_img_v1=PROJECT_ROOT / Path(f_cfg["temp_folder_img_v1"]),
            temp_img_v2=PROJECT_ROOT / Path(f_cfg["temp_folder_img_v2"]),
            temp_final_v1=PROJECT_ROOT / Path(f_cfg["temp_final_img_v1"]),
            temp_final_v2=PROJECT_ROOT / Path(f_cfg["temp_final_img_v2"]),
            temp_downloads=PROJECT_ROOT / Path(f_cfg["temp_folder_final"]),
            to_send=PROJECT_ROOT / Path(f_cfg["folder_to_send"])
        ),
        shapes=ShapefilePaths(
            countries=PROJECT_ROOT / Path(s_cfg["path_countries"]),
            central_countries=PROJECT_ROOT / Path(s_cfg["path_central_countries"]),
            sea=PROJECT_ROOT / Path(s_cfg["path_sea"])
        ),
        api=Clim4CastConfig(
            base_url=cfg["clim4cast"]["base_url"],
            username=username,
            password=password
        ),
        source_path=Path(cfg["path_to_source"]),
        templates_path=PROJECT_ROOT / Path(cfg["path_to_tamplates"]),
        frame_raster=PROJECT_ROOT / Path(cfg["frame_to_raster"]),
        font_path=PROJECT_ROOT / Path(cfg["font_path"]),
        dry_run=dry_run
    )


def _validate_paths_exist(config: AppConfig) -> None:
    """
    Validate that all required files and resources exist on disk.
    """
    paths_to_check = {
        "countries": config.shapes.countries,
        "central_countries": config.shapes.central_countries,
        "sea": config.shapes.sea,
        "source_path": config.source_path,
        "templates_path": config.templates_path,
        "frame_raster": config.frame_raster,
        "font_path": config.font_path,
    }
    missing_files = [path for path in paths_to_check.values() if not path.exists()]
    if missing_files:
        raise ValueError(
            f"Missing required files: {', '.join(str(mf) for mf in missing_files)}"
        )


def load_app_config(config_path: Path = DEFAULT_CONFIG_PATH) -> AppConfig:
    """
    Load application configuration, merging YAML and Environment variables
    """
    load_dotenv(PROJECT_ROOT / ".env")

    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
        _validate_structure(cfg)

    path_config = _build_app_config(cfg)

    _validate_paths_exist(path_config)

    return path_config
