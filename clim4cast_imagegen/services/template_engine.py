from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
import logging
from multiprocessing import cpu_count
from pathlib import Path

from clim4cast_imagegen.core.config import AppConfig
from clim4cast_imagegen.services.layout_engine import combine_maps_with_layout
from clim4cast_imagegen.utils.palette_utils import select_palette
from clim4cast_imagegen.utils.pathname_utils import background_type_from_template
from clim4cast_imagegen.io.local_storage import find_png_files_grouped_by_dir, ensure_dir


def generate_templates(
        config: AppConfig,
        visualizations: dict,
        logger: logging.Logger,
        ) -> None:
    """
    Paralel template generation.
    """

    templates = find_png_files_grouped_by_dir(
        config.templates_path,
        )
    max_workers = min(cpu_count() - 1 if cpu_count() > 1 else 1, 8)

    logger.info(f"Template generation using {max_workers} workers")

    for relative_dir, backgrounds in templates.items():
        target_dir = config.folders.temp_downloads / relative_dir

        ensure_dir(target_dir)

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

    background_type = background_type_from_template(background)

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
