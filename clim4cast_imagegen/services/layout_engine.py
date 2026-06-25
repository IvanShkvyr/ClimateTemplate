import logging
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from clim4cast_imagegen.io.image_io import open_rgba, save_image


def combine_maps_with_layout(
                            background_path: Path,
                            maps_list: list[Path],
                            labels_list: list[str],
                            output_path: Path,
                            font_path: Path,
                            logger: logging.Logger,
                            ) -> None:
    """
    Combines map images with a background layout and adds labels.

    This function places map images on a background layout, arranges them in a
    grid, and adds labels below each map. It then saves the final composition to
    a specified output file.

    Args:
        background_path (Path): The path to the background image.
        maps_list (list[Path]): A list of paths to the map images to be added.
        labels_list (list[str]): A list of labels corresponding to each map.
        output_path (Path): The path where the final composition will be saved.
        font_path (str, optional): The path to the font file used for labels.

    Returns:
        None: The function saves the final layout as a PNG file to the specified
            output path.
    """
    background = open_rgba(background_path)

    # Specify positioning and dimensions for maps and labels
    start_x = 24
    start_y = 94
    map_width = 850
    map_height = 906
    step_x = map_width + 18  # Horizontal step between maps
    step_y = map_height + 122  # Vertical step

    # Create a drawing object for adding labels
    draw = ImageDraw.Draw(background)
    font = ImageFont.truetype(str(font_path), size=62)

    # Iterate through maps and place them on the background
    for idx, (map_path, label) in enumerate(zip(maps_list, labels_list)):
        # Calculate position
        row = idx // 5  # Create a new row every 5 maps
        col = idx % 5   # Place maps in a horizontal line (max 5 in a row)

        x = start_x + col * step_x
        y = start_y + row * step_y

        # Open map image
        with Image.open(map_path) as map_image:
            map_rgba = map_image.convert("RGBA").resize((map_width, map_height))

            # Paste the map on the background
            background.paste(map_rgba, (x, y), map_rgba)

        # Add label below the map
        label_x = x + 42
        label_y = y - 79
        draw.text((label_x, label_y), label, fill="black", font=font)

    # Save the final image
    save_image(
            background,
            output_path,
            format="PNG",
            optimize=True,
            dpi=(300, 300)
            )
    logger.debug(f"Layout saved to {output_path}")


def process_image(src_path: Path, dst_path: Path, logger) -> None:
    """
    Opens an image, convert it to RGB, and saves as PNG
    """
    try:
        with Image.open(src_path) as img:
            img.convert("RGB").save(dst_path, "PNG", compress_level=4)
    except Exception as e:
        logger.error(f"Failed to process {src_path}: {e}")
