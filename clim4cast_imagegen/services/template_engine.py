from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
import logging
from multiprocessing import cpu_count
from pathlib import Path
import os

from clim4cast_imagegen.core.config import AppConfig
from clim4cast_imagegen.services.layout_engine import combine_maps_with_layout
from clim4cast_imagegen.utils.palette_utils import select_palette


def collect_templates(template_root: Path) -> dict:
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
        config: AppConfig,
        visualizations: dict,
        logger: logging.Logger,
        ) -> None:
    """
    Paralel template generation.
    """

    templates = collect_templates(
        config.templates_path,
        )
    max_workers = min(cpu_count() - 1 if cpu_count() > 1 else 1, 8)

    logger.info(f"Template generation using {max_workers} workers")

    for relative_dir, backgrounds in templates.items():
        target_dir = config.folders.temp_downloads / relative_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        layout = select_palette(relative_dir, visualizations)

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(
                    process_single_background,
                    background,
                    layout,
                    target_dir,
                    config.font_path,
                )
                for background in backgrounds
            ]

            for future in as_completed(futures):
                try:
                    future.result()

                except Exception as exc:
                    logger.exception(
                        f"Template worker failed: {exc}"
                    )


def process_single_background(
        background: Path,
        lauout_map,
        work_folder: Path,
        font_path: Path,
        ) -> None:
    """
    Worker function executed in a separate process.
    One background = one process
    """
    logger = logging.getLogger("template_worker")

    background_type = background.stem

    # Adjust background type if it contains "AW"
    if "AW" in background_type:
        background_type = background_type[3:-2]
    else:
        background_type = background_type[3:]

    try:
        img_list = lauout_map[background_type]
    except KeyError:
        logger.warning(
            f"Background type {background_type} not found in layout."
            )
        return
    
    date_labels = []

    # Extract date labels from image filenames
    for img in img_list:
        date = img.stem.split("_")[-1]

        formatted_date = datetime.strptime(
                                            date, "%Y-%m-%d"
                                            ).strftime("%d.%m.%Y")

        date_labels.append(formatted_date)
    
    if "DFM" in background_type:
        background_type = background_type.replace("DFM", "DFM_")
    if "AW" in background_type:
        background_type += "cm"

    # Define the output path for the composite image
    out_comp_file = work_folder / f"{background_type}.png"


    combine_maps_with_layout(
                            background,
                            img_list,
                            date_labels,
                            out_comp_file,
                            font_path,
                            logger=logger,
                            )
