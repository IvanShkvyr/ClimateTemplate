import logging
from pathlib import Path
import os

from src.data_loader import remove_local_directory
from src.data_processor import (
    ensure_directories_exist, process_backgrounds, ensure_directory_exists
    )
from src.data_visualizer import select_palette


def prepere_enviroment(config: dict, logger: logging.Logger) -> dict:
    """
    Prepare temporary working directories.
    Clean previous temp folder and recreates directory structure.
    """
    folders_cfg = config["folders_paths"]

    temp_root = folders_cfg["temp_folder"]

    if Path(temp_root).exists():
        remove_local_directory(temp_root)
        logger.info(f"Previous temporary directory removed.")


    # Define directories with STABLE semantic keys
    directories = {
        "temp_root": Path(temp_root),
        "cropped": Path(folders_cfg["temp_folder_crop"]),
        "transformed": Path(folders_cfg["temp_folder_trans"]),
        "reclassified": Path(folders_cfg["temp_polder_rec"]),
        "normal_data": Path(folders_cfg["temp_folder_img_v1"]),
        "reduced_data": Path(folders_cfg["temp_folder_img_v2"]),
        "final_normal": Path(folders_cfg["temp_final_img_v1"]),
        "final_reduced": Path(folders_cfg["temp_final_img_v2"]),
        "final_root": Path(folders_cfg["temp_folder_final"]),
        "folder_to_send": Path(folders_cfg["folder_to_send"]),
    }

    # Create all directories
    ensure_directories_exist(directories.values())
    logger.info("New temp directory structure created.")

    return directories


def cleanup(directories: dict, logger: logging.Logger) -> None:
    """
    Cleanup temporary resources after pipeline execution
    """
    temp_root = directories.get("temp_root")

    if temp_root and temp_root.exists():
        remove_local_directory(temp_root)
        logger.info("Temporary directory cleaned up.")
    else:
        logger.info("No temporary directory to clean up.")


def collect_templates(template_root: Path, directories: dict) -> dict:
    """
    Collect all template PNG files grouped by target folder.
    """
    templates = {}

    for root, _, files in os.walk(template_root):
        pngs = [Path(root) / f for f in files if f.endswith(".png")]

        if pngs:
            relative_path = Path(root).relative_to(template_root)
            target_dir = Path(relative_path)
            templates[target_dir] = pngs
    
    return templates


def generate_templates(
        config: dict,
        visualizations: dict,
        directories: dict,
        logger,
        ):
    """
    Orchestrates template background generation.
    """
    templates = collect_templates(Path(config["path_to_tamplates"]), directories)

    logger.info("Start processing templates")

    for relative_dir, template_files in templates.items():
        target_dir = Path(directories["final_root"]) / relative_dir
        ensure_directory_exists(target_dir)

        palette_layout = select_palette(relative_dir, visualizations)

        process_backgrounds(
            list_of_background=template_files,
            list_for_background_layout=palette_layout,
            work_folder=target_dir,
            logger=logger,
        )
