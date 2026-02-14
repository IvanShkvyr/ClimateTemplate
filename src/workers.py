
from datetime import datetime
from pathlib import Path
import logging

from src.data_processor import combine_maps_with_layout


def process_singl_background(
        background: Path,
        lauout_map,
        work_folder: Path,
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
                            logger=logger,
                            )



