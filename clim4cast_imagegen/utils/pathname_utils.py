from datetime import datetime
import logging
from pathlib import Path
from typing import Optional


def extract_date(path: Path, logger: logging.Logger) -> datetime:
    """
    Extract a date from the file name
    """
    stem = path.stem
    date_part = stem.split("_")[-1]
    try:
        return datetime.strptime(date_part, "%Y-%m-%d")
    except ValueError:
        logger.warning(f"Skipping a file without a date: {path}")
        return datetime.min
    

def get_background_type(path: Path) -> str:
    """
    Extract and normalize the background type from a file path.
    """
    background_type = path.stem

    # Adjust background type if it contains "AW"
    if "AW" in background_type:
        background_type = background_type[3:-2]
    else:
        background_type = background_type[3:]

    return background_type


def normalize_dfm_single_part(part: str) -> str:
    """
    Normalizes name parts by fixing DFM prefix

    Example:
        DFM100 -> DFM_100
    """
    if part.startswith("DFM") and len(part) > 3:
        return f"DFM_{part[3:]}"
    return part


def normalize_dfm_name_parts(parts: list[str]) -> list[str]:
    """
    Normalizes name parts by fixing DFM prefix

    Example:
        DFM100 -> DFM_100
    """
    return [normalize_dfm_single_part(p) for p in parts]


def build_new_filename(path: Path, index: int) -> str:
    """
    Builds a new filename based on the original name and index
    """
    name_parts = path.stem.split("_")[:-1]
    name_parts = normalize_dfm_name_parts(name_parts)

    result = "_".join(name_parts) + f"_{index}.png"

    return result
