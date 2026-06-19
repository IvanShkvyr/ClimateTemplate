from dataclasses import asdict
from datetime import date, timedelta
import logging
from pathlib import Path
import shutil
from typing import Iterable
import time

from src.core.constants import PARAMETERS, RETRY_INTERVAL
from src.core.config import AppConfig


def prepare_environment(config: AppConfig, logger: logging.Logger) -> None:
    """
    Prepare temporary working directories.
    Clean previous temp folder and recreates directory structure.
    """
    temp_root = config.folders.temp

    if temp_root.exists():
        shutil.rmtree(temp_root)
        logger.info(f"Previous temporary directory removed.")

    # Creating all subfolders described in FoldersConfig
    for flder_path in asdict(config.folders).values():
        flder_path.mkdir(parents=True, exist_ok=True)

    logger.info(f"Environment prepared. Directory structure recreated.")


def cleanup(config: AppConfig, logger: logging.Logger) -> None:
    """
    Cleanup temporary resources after pipeline execution
    """
    temp_root = config.folders.temp

    if temp_root and temp_root.exists():
        shutil.rmtree(temp_root)
        logger.info("Temporary directory cleaned up.")
    else:
        logger.info("No temporary directory to clean up.")


def create_data_folder_path(main_path: Path, today: date) -> Path:
    """
    Create a path to a folder based on the current date.

    This function takes the main path as input and appends the current date
    in the format 'YYYY-MM-DD' to it, creating a final path for the data folder.
    
    Args:
        main_path (Path): The base directory path where the data folder will be
            created.
        today (date): The specific date used to generate the folder path, in
            'YYYY-MM-DD' format.

    Returns:
        Path: complete path to the data folder with the current date appended
    """
    year = today.strftime("%Y")
    day = today.strftime("%Y-%m-%d")

    # Combine the main path with the current date
    final_path = main_path / year / day

    return final_path


def grab_files(
                directory_path: Path,
                parameters: Iterable[str] = PARAMETERS,
                extensions: tuple = (".tif", )
                ) -> Iterable[Path]:
    """
    Searches a given directory and its subdirectories for files with specific
    extensions and names that match any of the parameters in the provided
    dictionary.

    Args:
        directory_path (str): The directory path where the search will begin.
        parameters (dict): A dictionary containing parameters that should be
            present in the file name (default is PARAMETERS).
        extensions (set): A tuple containing file extensions to search for
            (default is (".tif",)).

    Returns:
        Iterable[Path]: A generator of Path objects pointing to files that match
          the given criteria.
    """
    ext_set = {e.lower() for e in extensions}

    # Loop through all elements in the directory and its subdirectories
    for element in directory_path.rglob("*"):
        # Skip files that don't match the desired extensions
        if element.suffix.lower() in ext_set:
            if any(param in element.stem for param in parameters):
                yield element
 

def wait_for_input_data(
        config: AppConfig,
        logger: logging.Logger,
        retry_interval: int = RETRY_INTERVAL
        ) -> Path:
    """
    Wait until today's input data folder exists
    """
    path_to_source = config.source_path
    today = date.today()

    # Creating a path to the data folder
    path_to_data = create_data_folder_path(path_to_source, today)


    while not (path_to_data).exists():
        logger.warning(f"Input data folder not found."
                f"Image generation process will retry in"
                f" {int(retry_interval//60)} minutes.")
        time.sleep(retry_interval)

    return path_to_data
