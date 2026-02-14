from datetime import datetime
import logging
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

import geopandas as gpd
from matplotlib.colors import (
    BoundaryNorm, ListedColormap, Normalize, LinearSegmentedColormap
    )
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import rasterio
from rasterio.plot import show


from src.data_loader import grab_files, load_data_from_mask_raster, load_config
from src.process_raster import process_rasters


path_config = load_config("config.yaml")

font_path = path_config["font_path"]


def combine_maps_with_layout(
                            background_path: Path,
                            maps_list: list[Path],
                            labels_list: list[str],
                            output_path: Path,
                            logger: logging.Logger,
                            font_path: str = font_path,
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
    # Load the background layout
    background = Image.open(background_path).convert("RGBA")

    # Specify positioning and dimensions for maps and labels
    start_x = 24
    start_y = 94
    map_width = 850
    map_height = 906
    step_x = map_width + 18  # Horizontal step between maps
    step_y = map_height + 122  # Vertical step

    # Create a drawing object for adding labels
    draw = ImageDraw.Draw(background)
    font = ImageFont.truetype(font_path, size=62)

    # Iterate through maps and place them on the background
    for idx, (map_path, label) in enumerate(zip(maps_list, labels_list)):
        # Calculate position
        row = idx // 5  # Create a new row every 5 maps
        col = idx % 5   # Place maps in a horizontal line (max 5 in a row)

        x = start_x + col * step_x
        y = start_y + row * step_y

        # Open map image
        map_image = Image.open(map_path).convert("RGBA")
        map_image = map_image.resize((map_width, map_height))

        # Paste the map on the background
        background.paste(map_image, (x, y))

        # Add label below the map
        label_x = x + 42
        label_y = y - 79
        draw.text((label_x, label_y), label, fill="black", font=font)

    # Save the final image
    background.save(output_path, "PNG", optimize=True, dpi=(300, 300))
    logger.debug(f"Layout saved to {output_path}")



def convert_png_to_jpg(out_comp_file: str, jpg_file: str) -> None:
    """
    Converts a PNG image to a JPG format with compression.

    Args:
        out_comp_file (str): Path to the input PNG file.
        jpg_file (str): Path where the converted JPG file will be saved.

    Returns:
        None: The function saves the converted JPG file to the specified
            location.
    """
    # Convert input paths to Path objects
    out_comp_file = Path(out_comp_file)
    jpg_file = Path(jpg_file)

    try:
        # Open the PNG image
        with Image.open(out_comp_file) as img:
            # Convert the image to RGB format
            rgb_img = img.convert("RGB")

            # Save the image in JPG format with 50% quality to reduce file size
            rgb_img.save(jpg_file, "JPEG", quality=50)

            print(f"Converted and compressed: {jpg_file}")
    except Exception as e:
        print(f"Error during conversion: {e}")


def create_visualization_countinious_with_shapefiles(
                                raster_file: str, 
                                final_path: str, 
                                colors_list: list[tuple], 
                                boundaries: list[float], 
                                countries_shapefile: gpd.GeoDataFrame, 
                                central_countries_shapefile: gpd.GeoDataFrame, 
                                sea_shapefile: gpd.GeoDataFrame,
                                continuous: bool = True
                                ) -> None:
    """
    Creates a visualization by overlaying raster data with shapefiles and
    saving the output as a PNG image. Works with both classified and continuous
    data.

    Args:
        raster_file (str): The path to the raster file to be visualized.
        final_path (str): The path where the output PNG image will be saved.
        colors_list (List[tuple]): A list of RGB colors to represent the data
            values at boundaries.
        boundaries (List[float]): A list of boundaries for color mapping. For
            continuous data, these define where each color in colors_list should
            be placed.
        countries_shapefile (gpd.GeoDataFrame): A GeoDataFrame representing the
            boundaries of countries.
        central_countries_shapefile (gpd.GeoDataFrame): A GeoDataFrame
            representing the boundaries of central countries.
        sea_shapefile (gpd.GeoDataFrame): A GeoDataFrame representing the
            boundaries of seas.
        continuous (bool, optional): If True, uses a continuous color gradient
            between boundaries. If False, uses discrete classes.

    Returns:
        None: The function saves the resulting plot to the specified
            `final_path` as a PNG image.
    """
    # Read the raster file
    with rasterio.open(raster_file) as src:
        raster_data = src.read(1)
        transform = src.transform
        nodata_value = src.nodata

    # Create a mask for NoData values and -999 values
    mask = (raster_data == -999)
    if nodata_value is not None:
        mask = np.logical_or(mask, raster_data == nodata_value)
    
    # Apply the mask
    masked_data = np.ma.masked_where(mask, raster_data)
    
    # Normalize colors to 0-1 range for matplotlib
    normalized_colors = [tuple(c / 255.0 for c in color) for color in colors_list]
    
    if continuous:
        # Create a mask for NoData values 
        no_data_mask = np.logical_or(raster_data == -999, raster_data == -1)
        
        # Calculate color positions based on boundaries 
        min_val = boundaries[1]  # First valid boundary after NoData
        max_val = boundaries[-1]
        positions = [(boundary - min_val) / (max_val - min_val) for boundary in boundaries[1:]]
        positions = [0] + positions  # Add 0 for the first color
        
        # Create a color map
        cmap = LinearSegmentedColormap.from_list("custom_cmap", 
                            list(zip(positions, normalized_colors[1:])))
        
        # Create a color map
        norm = Normalize(vmin=min_val, vmax=max_val)
        
        # Apply mask for NoData values
        masked_data = np.ma.masked_where(no_data_mask, raster_data)
    
    else:
        # For discrete classes, use the original approach
        cmap = ListedColormap(normalized_colors)
        norm = BoundaryNorm(boundaries, cmap.N, extend='max')

    # Create a figure for the visualization
    fig, ax = plt.subplots(figsize=(21, 21), dpi=300)

    # Set the extent of the plot based on the raster transform
    ax.set_xlim([transform[2], transform[2] + src.width * transform[0]])
    ax.set_ylim([transform[5] + src.height * transform[4], transform[5]])

    # Show the raster data with the colormap and normalization
    show(masked_data, ax=ax, cmap=cmap, norm=norm, transform=transform)

    # Overlay the shapefiles on the plot
    sea_shapefile.plot(
                    ax=ax,
                    facecolor=(156/255, 156/255, 156/255),
                    edgecolor='none',
                    linewidth=3
                    )
    countries_shapefile.plot(
                            ax=ax,
                            facecolor='none',
                            edgecolor='black',
                            linewidth=1.2
                            )
    central_countries_shapefile.plot(
                                    ax=ax,
                                    facecolor='none',
                                    edgecolor='black',
                                    linewidth=3.2
                                    )

    ax.set_axis_off()
    
    # Save the final visualization as a PNG image
    plt.savefig(
                final_path,
                format='png',
                dpi=300,
                bbox_inches='tight',
                pad_inches=-0.04
                )
    # Close the figure to free memory
    plt.close(fig)


def generate_base_raster(
        path_to_data: str,
        config: dict,
        directories: dict,
        logger: logging.Logger,
        ) -> list:
    """
    Generate base raster images from source data.
    """
    # Create file lists
    list_of_rasters = grab_files(path_to_data)
    logger.info(f"Found {len(list_of_rasters)} source files.")

    # Create mask shape
    frame_to_raster = config["frame_to_raster"]
    mask_shape = load_data_from_mask_raster(frame_to_raster)

    logger.info(f"Start process rasters")
    list_of_img = process_rasters(
        list_of_rasters,
        mask_shape,
        directories['cropped'],
        directories['transformed'],
        )
    logger.info(f"All base rasters were clipped, converted, and saved "
                f"to {directories['cropped']}")
    
    return list_of_img


def ensure_directory_exists(directory_path: str) -> Path:
    """
    Ensure that the specified exists. If not? create it.
    
    Parameters:
        directory_path (str or Path): The path to the folder to check or create.
        
    Returns:
        Path: The Path object of the ensured directory.
    """
    path = Path(directory_path)

    # Ensure that the directory exists, if not create it
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

    return path


def ensure_directories_exist(folders: list) -> dict:
    """
    Checks if the specified directories exist, and creates them if they do not.

    Args:
        folders (list): A list of folder paths that need to be checked and
            created if necessary.

    Returns:
        dict: A dictionary where the key is the folder path and the value is
            a boolean indicating whether the folder was created (True) or
            already existed (False).
    """
    return {folder: ensure_directory_exists(folder) for folder in folders}


def process_backgrounds(
        list_of_background: list[Path],
        list_for_background_layout: dict[str, list[Path]],
        work_folder: Path,
        logger: logging.Logger,
        ) -> None:
    """
    Processes backgrounds and combines maps into a layout.

    This function processes a list of background images, extracts the date from 
    the file names, and combines the background with its corresponding maps 
    (from `list_for_background_layout`) into a composite image for each
    background type.
    
    Args:
        list_of_background (list[Path]): A list of paths to background images.
        list_for_background_layout (dict[str, list[Path]]): A dictionary where
            keys are background types, and values are lists of paths to image
            files that should be combined with the background.
        work_folder (Path): The folder where the combined images will be saved.

    Returns:
        None: The function does not return anything. It generates and saves
            composite images.
    """
    for background in list_of_background:
        date_labels = []
        background_type = background.stem

        # Adjust background type if it contains "AW"
        if "AW" in background_type:
            background_type = background_type[3:-2]
        else:
            background_type = background_type[3:]

        try:
            img_list = list_for_background_layout[background_type]
        except KeyError:
            logger.warning(
                f"Background type {background_type} not found in layout."
                )
            continue

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
        


        # # Get the path. Move up two levels
        # de_folder = Path(out_comp_file).parent.parent

        # # Define the path to the "JPG" folder
        # path_to_jpg_folder = de_folder / "JPG"

        # # Ensure that the "JPG" folder exists, create it if necessary
        # ensure_directory_exists(path_to_jpg_folder)

        # # Construct the new path for the JPG file
        # jpg_file = de_folder / "JPG" / (Path(out_comp_file).stem + ".jpg")
        
        # # Convert the PNG file to JPG and save it in the specified location
        # convert_png_to_jpg(out_comp_file, jpg_file)

