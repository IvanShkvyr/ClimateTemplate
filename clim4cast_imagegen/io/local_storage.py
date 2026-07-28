import logging
import os
import shutil
from collections.abc import Iterable
from dataclasses import asdict
from datetime import date
from pathlib import Path

from clim4cast_imagegen.core.config import PROJECT_ROOT, AppConfig
from clim4cast_imagegen.core.constants import PARAMETERS

MARKER_FILE = PROJECT_ROOT / "state" / "last_processed.txt"


def prepare_environment(config: AppConfig, logger: logging.Logger) -> None:
    """
    Prepare temporary working directories.
    Clean previous temp folder and recreates directory structure.
    """
    temp_root = config.folders.temp

    if temp_root.exists():
        shutil.rmtree(temp_root)
        logger.info("Previous temporary directory removed.")

    # Creating all subfolders described in FoldersConfig
    for folder_path in asdict(config.folders).values():
        folder_path.mkdir(parents=True, exist_ok=True)

    logger.info("Environment prepared. Directory structure recreated.")


def cleanup(config: AppConfig, logger: logging.Logger) -> None:
    """
    Remove temporary resources after pipeline execution.
    """
    temp_root = config.folders.temp

    if temp_root and temp_root.exists():
        shutil.rmtree(temp_root)
        logger.info("Temporary directory cleaned up.")
    else:
        logger.info("No temporary directory to clean up.")


def create_data_folder_path(main_path: Path, today: date) -> Path:
    """Build the source data folder path for a given date."""
    year = today.strftime("%Y")
    day = today.strftime("%Y-%m-%d")

    # Combine the main path with the current date
    final_path = main_path / year / day

    return final_path


def iter_matching_files (
                directory_path: Path,
                parameters: Iterable[str] = PARAMETERS,
                extensions: tuple = (".tif", )
                ) -> Iterable[Path]:
    """
    Yield files under the root that match the given extensions and name parts.
    """
    ext_set = {e.lower() for e in extensions}

    # Loop through all elements in the directory and its subdirectories
    for element in directory_path.rglob("*"):
        # Skip files that don't match the desired extensions
        if element.suffix.lower() in ext_set:
            if any(param in element.stem for param in parameters):
                yield element


def find_input_data(
        config: AppConfig,
        logger: logging.Logger,
        ) -> Path | None:
    """
    Return today's input data folder if it exists, else None.
    """
    today = date.today()

    # Creating a path to the data folder
    path_to_data = create_data_folder_path(config.source_path, today)

    if path_to_data.exists():
        return path_to_data

    logger.info("Input data not ready yet.")

    return None


def find_png_files_grouped_by_dir(root: Path) -> dict[Path, list[Path]]:
    """Walk a directory tree and group PNG files by their relative folder."""
    grouped: dict[Path, list[Path]] = {}
    for current_dir, _, files in os.walk(root):
        pngs = [Path(current_dir) / f for f in files if f.endswith(".png")]
        if pngs:
            relative_path = Path(current_dir).relative_to(root)
            grouped[relative_path] = pngs
    return grouped


def ensure_dir(path: Path) -> None:
    """Create the directory and its parents if they do not exist."""
    path.mkdir(parents=True, exist_ok=True)


def is_already_processed(today: date, marker_file: Path = MARKER_FILE) -> bool:
    """Return True if the given date is already recorded as processed."""
    if not marker_file.exists():
        return False
    return marker_file.read_text().strip() == today.isoformat()


def mark_processed(today: date, marker_file: Path = MARKER_FILE) -> None:
    """Record today's date as processed (create the state dir if needed)."""
    marker_file.parent.mkdir(parents=True, exist_ok=True)
    marker_file.write_text(today.isoformat())
