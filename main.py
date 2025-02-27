from datetime import datetime

from src.data_loader import (
    load_config, load_shp, grab_files, load_data_from_mask_raster
    )
from src.data_processor import (
    ensure_directories_exist, process_rasters, process_backgrounds,
    process_raster_for_layout
)


path_config = load_config("config.yaml")

temp_folder = path_config["folders_paths"]["temp_folder"]
temp_folder_img = path_config["folders_paths"]["temp_folder_img"]
temp_polder_fig = path_config["folders_paths"]["temp_polder_fig"]
output_folder_img = path_config["folders_paths"]["output_folder_img"]
output_folder_png = path_config["folders_paths"]["output_folder_png"]

path_to_sours = path_config["path_to_sours"]

path_to_tamplates = path_config["path_to_tamplates"]
frame_to_raster = path_config["frame_to_raster"]

path_countrys = path_config["shapefiles_paths"]["path_countrys"]
path_central_countrys = path_config["shapefiles_paths"]["path_central_countrys"]
path_sea = path_config["shapefiles_paths"]["path_sea"]


def main():
    start_time = datetime.now()

    # Ensure necessary directories exist
    folders = [
        temp_folder,
        temp_folder_img,
        temp_polder_fig,
        output_folder_img,
        output_folder_png
        ]
    directories = ensure_directories_exist(folders)

    # Create file lists
    list_of_rasters = grab_files(path_to_sours)
    list_of_background = grab_files(path_to_tamplates, extensions=(".png",))

    # Create mask shape
    mask_shape = load_data_from_mask_raster(frame_to_raster)

    # Process rasters
    list_of_img = process_rasters(
        list_of_rasters,
        mask_shape,
        directories[temp_folder],
        directories[temp_folder_img]
        )

    # Load shapefiles
    countries_shapefile = load_shp(path_countrys)
    central_countries_shapefile = load_shp(path_central_countrys)
    sea_shapefile = load_shp(path_sea)

    # Process background layout
    list_for_background_layout = {}
    for raster_path in list_of_img:
        process_raster_for_layout(
            raster_path,
            list_for_background_layout,
            countries_shapefile,
            central_countries_shapefile,
            sea_shapefile,
            output_folder_img
            )

    # Process backgrounds
    process_backgrounds(
        list_of_background,
        list_for_background_layout,
        directories[output_folder_png],
        )

    # Calculate execution time
    end_time = datetime.now()
    print(f"Execution time: {end_time - start_time}")


if __name__ == "__main__":

    main()
