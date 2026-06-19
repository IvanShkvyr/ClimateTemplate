from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PaletteConfig:
    name: str
    palettes: dict
    temp_dir: Path
    final_dir: Path


def select_palette(
        target_folder: Path,
        visualizations: dict[str, Any]
        ) -> dict[str, Any]:
    """
    Select visualization layout based on target folder structure.
    """
    parent_name = target_folder.parent.name

    if parent_name not in visualizations:
        raise ValueError(f"Unknown palette folder: {parent_name}")

    return visualizations[parent_name]




