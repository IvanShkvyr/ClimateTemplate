from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count
import os

from src.workers import process_singl_background
from src.enviroment import collect_templates
from src.data_visualizer import select_palette
from src.data_processor import ensure_directory_exists


def generate_templates(
        config,
        visualizations,
        directories,
        logger,
        ) -> None:
    """
    Paralel template generation.
    """

    templates = collect_templates(Path(config["path_to_tamplates"]), directories)
    max_workers = min(cpu_count() - 1 if cpu_count() > 1 else 1, 8)

    logger.info(f"Template generation using {max_workers} workers")

    for relative_dir, template_files in templates.items():
        target_dir = Path(directories["final_root"]) / relative_dir
        ensure_directory_exists(target_dir)

        palette_layout = select_palette(relative_dir, visualizations)

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = [
executor.submit()
            ]


    #     process_backgrounds(
    #         list_of_background=template_files,
    #         list_for_background_layout=palette_layout,
    #         work_folder=target_dir,
    #         logger=logger,
    #     )
