from datetime import date, datetime
import os

from dotenv import load_dotenv

from src.data_loader import (
    create_data_folder_path, load_config, load_shp, grab_files,
    load_data_from_mask_raster, remove_directory
    )
from src.data_processor import (
    ensure_directories_exist, process_rasters, process_backgrounds,
    process_raster_for_layout
)
from src.sftp_connection import (
    connect_to_sftp, disconnect_from_sftp, upload_directory
    )


load_dotenv()

sftp_host = os.getenv("HOST")
sftp_username = os.getenv("USERNAME")
sftp_password = os.getenv("PASSWORD")
sftp_port = os.getenv("PORT")

path_config = load_config("config.yaml")

temp_folder = path_config["folders_paths"]["temp_folder"]
temp_cropped_images = path_config["folders_paths"]["temp_folder_crop"]
temp_folder_trans = path_config["folders_paths"]["temp_folder_trans"]
temp_polder_rec = path_config["folders_paths"]["temp_polder_rec"]
temp_folder_img = path_config["folders_paths"]["temp_folder_img"]
temp_folder_png = path_config["folders_paths"]["temp_folder_png"]

path_to_sours = path_config["path_to_sours"]

path_to_tamplates = path_config["path_to_tamplates"]
frame_to_raster = path_config["frame_to_raster"]

path_countrys = path_config["shapefiles_paths"]["path_countrys"]
path_central_countrys = path_config["shapefiles_paths"]["path_central_countrys"]
path_sea = path_config["shapefiles_paths"]["path_sea"]

remote_dir = path_config["remote_dir"]


def main():
    start_time = datetime.now()

    # Get today's date and format the date as YYYY-MM-DD
    today = date.today()

    # Creating a path to the data folder
    path_to_data = create_data_folder_path(path_to_sours, today)

    # Ensure necessary directories exist
    folders = [
        temp_cropped_images,
        temp_folder_trans,
        temp_polder_rec,
        temp_folder_img,
        temp_folder_png
        ]
    directories = ensure_directories_exist(folders)

    # Create file lists
    list_of_rasters = grab_files(path_to_data)
    list_of_background = grab_files(path_to_tamplates, extensions=(".png",))

    # Create mask shape
    mask_shape = load_data_from_mask_raster(frame_to_raster)

    # Process rasters
    list_of_img = process_rasters(
        list_of_rasters,
        mask_shape,
        directories[temp_cropped_images],
        directories[temp_folder_trans]
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
            temp_folder_img
            )

    # Process backgrounds
    process_backgrounds(
        list_of_background,
        list_for_background_layout,
        directories[temp_folder_png],
        )

    # # Establishing a connection to the SFTP server
    # sftp = connect_to_sftp(sftp_host, sftp_username, sftp_password, int(sftp_port))

    # # NOTE: Use this path for testing (static folder name)
    # remote_date_path = os.path.join(remote_dir, "test")

    # # NOTE: Use the following line for production (dynamic folder name based on the current date)
    # # remote_date_path = os.path.join(remote_dir, today.strftime("%Y-%m-%d"))

    # # Uploading a local folder to SFTP
    # upload_directory(sftp, temp_folder_png, remote_date_path)

    # disconnect_from_sftp(sftp)

    remove_directory(temp_folder)

    # Calculate execution time
    end_time = datetime.now()
    print(f"Execution time: {end_time - start_time}")

if __name__ == "__main__":

    main()
