from pathlib import Path

import geopandas as gpd
from matplotlib.colors import BoundaryNorm, ListedColormap, Normalize
import matplotlib.pyplot as plt
import numpy as np
from pyproj import CRS
import rasterio
from rasterio.plot import show
from rasterio.warp import reproject, Resampling, calculate_default_transform

from src.constants import CRS_FOR_DATA, PALETTES
from src.data_loader import read_and_clip_raster
from src.data_visualizer import combine_maps_with_layout


def convert_coordinate_systen_in_raster(
                                        target_crs: CRS,
                                        input_path: str,
                                        output_path: str
                                        ) -> None:
    """
    Converts the coordinate system of the input raster to the specified CRS 
    and saves the reprojected raster to the given output path.

    Args:
        crs_mercator (CRS): The target coordinate reference system (CRS) to
            which the raster should be converted. Typically, this would be the
            Web Mercator projection (EPSG:3857).
        input_path (str): The file path of the input raster that needs to be
            reprojected.
        output_path (str): The file path where the reprojected raster will
            be saved.

    Returns:
        None: The function performs the reprojecting and saves the resulting
            raster to the specified output path.
    """

    # Open the source raster to check its CRS and other properties
    with rasterio.open(input_path) as src:

        # Check if the CRS of the raster is different from the target CRS
        if src.crs != target_crs:
            # Calculate the transformation needed to convert the current CRS
            # to target CRS
            transform, width, height = calculate_default_transform(
                src.crs, target_crs, src.width, src.height, *src.bounds
            )
            nodata_value = src.nodata

            # Open a new raster file for saving the reprojected data
            with rasterio.open(output_path, "w", driver="GTiff",
                            count=1, dtype=src.dtypes[0],
                            crs=target_crs, transform=transform,
                            width=width, height=height,
                            nodata=nodata_value) as dst:
                
                # Reproject the data from the source CRS to the target CRS
                reproject(
                    source=rasterio.band(src, 1),
                    destination=rasterio.band(dst, 1),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=target_crs,
                    resampling=Resampling.nearest
                )

            # Print a success message once the raster is reprojected and saved
            print(f"Raster reprojected and saved to {output_path}")



def create_visualization_with_shapefiles(
                                raster_file: str, 
                                final_path: str, 
                                colors_list: list[tuple], 
                                classes: list[int], 
                                countries_shapefile: gpd.GeoDataFrame, 
                                central_countries_shapefile: gpd.GeoDataFrame, 
                                sea_shapefile: gpd.GeoDataFrame
                                ) -> None:
    """
    Creates a visualization by overlaying raster data with shapefiles and
    saving the output as a PNG image.

    Args:
        raster_file (str): The path to the raster file to be visualized.
        final_path (str): The path where the output PNG image will be saved.
        colors_list (List[tuple]): A list of RGB colors to represent the unique
            raster classes.
        classes (List[int]): A list of unique classes in the raster data, used
            to filter the color palette.
        countries_shapefile (gpd.GeoDataFrame): A GeoDataFrame representing the
            boundaries of countries.
        central_countries_shapefile (gpd.GeoDataFrame): A GeoDataFrame
            representing the boundaries of central countries.
        sea_shapefile (gpd.GeoDataFrame): A GeoDataFrame representing the
            boundaries of seas.

    Returns:
        None: The function saves the resulting plot to the specified
            `final_path` as a PNG image.
    """
    # Read the raster file
    with rasterio.open(raster_file) as src:
        raster_data = src.read(1)
        transform = src.transform
        nodata_value = src.nodata

    # Get unique values (classes) from the raster data
    unique_classes = np.unique(raster_data)

    # Filter the boundaries and colors only for the unique classes
    filtered_boundaries = [b for b in classes if b in unique_classes]
    filtered_colors = [colors_list[i]
                for i in range(len(classes)) if classes[i] in unique_classes]

    # If more than one unique class, create a proper colormap and normalization
    if len(filtered_boundaries) > 1:
        cmap = ListedColormap(
            [tuple(c / 255.0 for c in color)for color in filtered_colors]
            )
        norm = BoundaryNorm(filtered_boundaries, cmap.N, extend='max')

    else:
        # If there's only one unique class, use a single color
        cmap = ListedColormap([tuple(c / 255.0 for c in filtered_colors[0])])
        norm = Normalize(
                        vmin=filtered_boundaries[0] - 0.5,
                        vmax=filtered_boundaries[0] + 0.5
                        )

    # Normalize the raster data values
    normalized_values = norm(raster_data)

    # Create a figure for the visualization
    fig, ax = plt.subplots(figsize=(21, 21), dpi=300)

    # Set the extent of the plot based on the raster transform
    ax.set_xlim([transform[2], transform[2] + src.width * transform[0]])
    ax.set_ylim([transform[5] + src.height * transform[4], transform[5]])

    # Mask NoData values and -999 values
    raster_data = np.ma.masked_where(raster_data == -999, raster_data)
    if nodata_value is not None:
        raster_data = np.ma.masked_equal(raster_data, nodata_value)

    # Show the raster data with the colormap and normalization
    show(normalized_values, ax=ax, cmap=cmap, transform=transform)

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


def process_rasters(
                    list_of_rasters: list[Path],
                    mask_shape: dict,
                    tump_folder: Path,
                    tump_folder_img: Path,
                    ) -> list[Path]:
    """
    Processes rasters by clipping them with a mask and converting their
    coordinate system.

    This function iterates through a list of raster files, clips each raster
    using a provided mask shape, and converts the coordinate system to a
    specified one. The processed rasters are saved in the specified temporary
    folders.

    Args:
        list_of_rasters (List[Path]): A list of raster file paths to be
            processed.
        mask_shape (dict): The shape used for clipping the rasters.
        tump_folder (Path): The temporary folder path where clipped rasters
            will be saved.
        tump_folder_img (Path): The temporary folder path where coordinate
            system converted rasters will be saved.

    Returns:
        List[Path]: A list of file paths for the processed rasters (with the
            converted coordinate system).
    """
    list_of_img = []
    for raster in list_of_rasters:
        # Define output paths for clipped raster and coordinate system converted
        # raster
        output_path = tump_folder / raster.name
        output_path_2 = tump_folder_img / raster.name
        # Clip raster based on the mask shape and save the result
        read_and_clip_raster(raster, mask_shape, output_path)
        # Convert the coordinate system of the raster and save the result
        convert_coordinate_systen_in_raster(
                                            CRS_FOR_DATA,
                                            output_path,
                                            output_path_2
                                            )
         # Append the processed raster to the list
        list_of_img.append(output_path_2)

    return list_of_img


def process_raster_for_layout(
                            raster_path: Path,
                            list_for_background_layout: dict[str, list],
                            countries_shapefile: gpd.GeoDataFrame,
                            central_countries_shapefile: gpd.GeoDataFrame,
                            sea_shapefile: gpd.GeoDataFrame,
                            work_folder: Path
                            ) -> None:
    """
    Processes a raster file for visualization and classification, and organizes
    the resulting image into background layout categories.

    This function processes a given raster file by:
    1. Extracting its type from the file name.
    2. Reclassifying the raster if necessary.
    3. Creating a visualization of the raster with specified shapefiles as
        overlays.
    4. Categorizing the processed image into a background layout group based
        on its type.

    Args:
        raster_path (Path): The path to the raster file to be processed.
        list_for_background_layout (Dict[str, list]): A dictionary that organizes processed raster images
            into categories based on their type for layout purposes.
        countries_shapefile (gpd.GeoDataFrame): A GeoDataFrame containing the boundaries of countries.
        central_countries_shapefile (gpd.GeoDataFrame): A GeoDataFrame containing the boundaries of central countries.
        sea_shapefile (gpd.GeoDataFrame): A GeoDataFrame containing the boundaries of seas.
        work_folder (Path): The folder where processed files will be saved.

    Returns:
        None: The function does not return any value. It modifies `list_for_background_layout` in place.
    """
    # Extract the type of raster from the file name
    raster_parts_name = raster_path.stem.split("_")
    raster_type = raster_parts_name[0]

    # Choose palette based on raster type
    if raster_type not in PALETTES:
        raise ValueError(f"Palette for type {raster_type} not found")

    # Load the palette and boundaries for the given raster type
    palettes = PALETTES[raster_type]
    boundaries = palettes["boundaries"]
    colors = palettes["colors"]
    classes = palettes["classes"]

    # If raster type is not "AWP" or "FWI", reclassify it
    if raster_type not in ["AWP", "FWI"]:
        raster_path = reclassify_raster(raster_path, work_folder, boundaries)

    img_path = Path(work_folder) / Path(raster_path).name

    # Create visualization with shapefiles as overlays
    create_visualization_with_shapefiles(
        raster_path,
        img_path,
        colors,
        classes,
        countries_shapefile,
        central_countries_shapefile,
        sea_shapefile,
    )

    # Determine the background type based on raster type
    if "AW" in raster_type:
        background_type = "_".join([raster_parts_name[0], raster_parts_name[1]])
        background_type = background_type[:-2]
    elif "FWI" in raster_type:
        background_type = "FWI_GenZ"
    else:
        background_type = raster_parts_name[0]

    if background_type not in list_for_background_layout:
        list_for_background_layout[background_type] = []

    # Append the image path to the appropriate background type category
    list_for_background_layout[background_type].append(img_path)


def process_backgrounds(
        list_of_background: list[Path],
        list_for_background_layout: dict[str, list[Path]],
        work_folder: Path,
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
            print(f"Background type {background_type} not found in layout.")
            continue

        # Extract date labels from image filenames
        for img in img_list:
            date = img.stem.split("_")[-1]
            date_labels.append(date)

        # Define the output path for the composite image
        out_comp_file = work_folder / f"{background_type}.png"
        combine_maps_with_layout(
                                background,
                                img_list,
                                date_labels,
                                out_comp_file
                                )


def reclassify_raster(
                    raster_path: Path, 
                    output_raster_path: Path, 
                    boundaries: list[float]
                    ) -> Path:
    """
    Reclassifies a raster based on specified boundaries and saves the output.

    This function reads an input raster, reclassifies its pixel values into 
    new classes based on the provided boundaries, and writes the reclassified
    raster to the specified output path. The new raster will have integer class
    values.

    Args:
        raster_path (Path): The path to the input raster file.
        output_raster_path (Path): The directory where the output raster file
            will be saved.
        boundaries (List[float]): A list of boundary values to define the
            reclassification bins.

    Returns:
        Path: The path to the saved reclassified raster file.
    """
    # Load the raster file
    with rasterio.open(raster_path) as src:
        raster_data = src.read(1)
        profile = src.profile
        # Default to -999 if NoData is not defined
        nodata_value = src.nodata if src.nodata is not None else -999.0
    
    # Reclassify the raster data based on the provided boundaries
    classes = np.digitize(raster_data, bins=boundaries, right=True) - 1
    
    
    final_path = Path(output_raster_path) / Path(raster_path).name

    # Update the profile with new data type and NoData value
    profile.update(dtype=rasterio.int16, count=1, nodata=nodata_value)

    # Write the reclassified raster to the output path
    with rasterio.open(final_path, 'w', **profile) as dst:
        dst.write(classes.astype(rasterio.int16), 1)

    return final_path


