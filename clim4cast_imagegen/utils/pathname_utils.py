from datetime import datetime
from pathlib import Path

from clim4cast_imagegen.core.exceptions import InvalidRasterDateError


def extract_date(path: Path) -> datetime:
    """Extract the date from a filename.

    Raise InvalidRasterDateError if the date is missing or invalid.
    """
    stem = path.stem
    date_part = stem.split("_")[-1]
    try:
        return datetime.strptime(date_part, "%Y-%m-%d")
    except ValueError as exc:
        raise InvalidRasterDateError(path) from exc


def background_type_from_template(path: Path) -> str:
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


def background_type_from_raster(
        raster_name_parts: list[str],
        ) -> str:
    """
    Build the background type key from raster filename parts.
    """
    if "AW" in raster_name_parts[0]:
        background_type = "_".join([raster_name_parts[0], raster_name_parts[1]])
        background_type = background_type[:-2]
    elif "FWI" in raster_name_parts[0]:
        background_type = "FWI_GenZ"
    else:
        background_type = raster_name_parts[0]

    return background_type


def normalize_dfm_single_part(part: str) -> str:
    """
    Add an underscore after the DFM prefix (DFM100 -> DFM_100).
    """
    if part.startswith("DFM") and len(part) > 3:
        return f"DFM_{part[3:]}"
    return part


def normalize_dfm_name_parts(parts: list[str]) -> list[str]:
    """
    Apply the DFM prefix fix to every part of a filename.
    """
    return [normalize_dfm_single_part(p) for p in parts]


def build_new_filename(path: Path, index: int) -> str:
    """
    Build a new filename from the original name and an index.
    """
    name_parts = path.stem.split("_")[:-1]
    name_parts = normalize_dfm_name_parts(name_parts)

    result = "_".join(name_parts) + f"_{index}.png"

    return result
