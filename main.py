from pathlib import Path
import sys
sys.path.append('D:/CzechGlobe/Task/ClimateTemplate')


from datetime import date, datetime
import os

from dotenv import load_dotenv

from src.data_loader import (
    create_data_folder_path, load_config, load_shp, grab_files,
    load_data_from_mask_raster, remove_local_directory
    )
from src.data_processor import (
    ensure_directories_exist, process_rasters, process_backgrounds,
    process_raster_for_layout, ensure_directory_exists
)
from src.connection import (
    connect_to_sftp, disconnect_from_sftp, remove_old_sftp_folders, 
    upload_directory_in_sftp, connect_to_ftp, upload_files_to_ftp,
    disconnect_from_ftp
    )
from src.constants import PALETTES_V1, PALETTES_V2


load_dotenv()

sftp_host = os.getenv("SFTP_HOST")
sftp_username = os.getenv("SFTP_USERNAME")
sftp_password = os.getenv("SFTP_PASSWORD")
sftp_port = os.getenv("SFTP_PORT")

ftp_host = os.getenv("FTP_HOST")
ftp_username = os.getenv("FTP_USERNAME")
ftp_password = os.getenv("FTP_PASSWORD")

path_config = load_config("config.yaml")

temp_folder = path_config["folders_paths"]["temp_folder"]
temp_cropped_images = path_config["folders_paths"]["temp_folder_crop"]
temp_folder_trans = path_config["folders_paths"]["temp_folder_trans"]
temp_polder_rec = path_config["folders_paths"]["temp_polder_rec"]
temp_folder_img_v1 = path_config["folders_paths"]["temp_folder_img_v1"]
temp_folder_img_v2 = path_config["folders_paths"]["temp_folder_img_v2"]
temp_folder_final = path_config["folders_paths"]["temp_folder_final"]

path_to_sours = path_config["path_to_sours"]

path_to_tamplates = path_config["path_to_tamplates"]
frame_to_raster = path_config["frame_to_raster"]

path_countrys = path_config["shapefiles_paths"]["path_countrys"]
path_central_countrys = path_config["shapefiles_paths"]["path_central_countrys"]
path_sea = path_config["shapefiles_paths"]["path_sea"]

remote_sftp_dir = path_config["remote_sftp_dir"]
remote_ftp_dir = path_config["remote_ftp_dir"]


def main():
    start_time = datetime.now()

    # # Get today's date and format the date as YYYY-MM-DD
    # today = date.today()

    # # Creating a path to the data folder
    # path_to_data = create_data_folder_path(path_to_sours, today)

    # NOTE TEST
    path_to_data = path_to_sours

    # Ensure necessary directories exist
    folders = [
        temp_cropped_images,
        temp_folder_trans,
        temp_polder_rec,
        temp_folder_img_v1,
        temp_folder_img_v2,
        temp_folder_final
        ]
    directories = ensure_directories_exist(folders)

    # Create file lists
    list_of_rasters = grab_files(path_to_data)

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

    # Process background layout for palette v1 (original CzechGlobe palette)
    list_for_background_layout_v1 = {}
    for raster_path in list_of_img:
        process_raster_for_layout(
            raster_path,
            list_for_background_layout_v1,
            countries_shapefile,
            central_countries_shapefile,
            sea_shapefile,
            temp_folder_img_v1,
            PALETTES_V1,
            )

    # Process background layout for palette v2
    list_for_background_layout_v2 = {}
    for raster_path in list_of_img:
        process_raster_for_layout(
            raster_path,
            list_for_background_layout_v2,
            countries_shapefile,
            central_countries_shapefile,
            sea_shapefile,
            temp_folder_img_v2,
            PALETTES_V2,
            )


    templates_dict = {}
    # Recursively go through all subfolders with templates 
    for root, _, files in os.walk(path_to_tamplates):
        template_files = [Path(root) / file for file in files if file.endswith(".png")]

        if template_files:
            # Determine the corresponding path in the result folder
            relative_path = Path(root).relative_to(path_to_tamplates)
            result_path = Path(temp_folder_final) / relative_path / "Figs"

            # Add to the dictionary  
            templates_dict[result_path] = template_files

    
    # Add generated rasters to templates  
    for target_folder, template_list in templates_dict.items():
        ensure_directory_exists(target_folder)

        # Determine which palette variant needs to be applied  
        result = os.path.basename(os.path.dirname(target_folder))
        if result == "templates_v1":
            list_for_background = list_for_background_layout_v1
        else:
            list_for_background = list_for_background_layout_v2

        # Process backgrounds
        process_backgrounds(
            template_list,
            list_for_background,
            target_folder,
            )

    # Establishing a connection to the SFTP server
    sftp = connect_to_sftp(
                        sftp_host, sftp_username, sftp_password, int(sftp_port)
                        )

    # NOTE: Use this path for testing (static folder name)
    remote_date_path = os.path.join(remote_sftp_dir, "test5")

    # # NOTE: Use the following line for production (dynamic folder name based on the current date)
    # # remote_date_path = os.path.join(remote_sftp_dir, today.strftime("%Y-%m-%d"))

    # Uploading a local folder to SFTP
    upload_directory_in_sftp(sftp, temp_folder_final, remote_date_path)

    # # NOTE:Deleting the oldest directory
    # # remove_old_sftp_folders(sftp, remote_sftp_dir, 7)

    disconnect_from_sftp(sftp)


    # # Establishing a connection to the FTP server
    # ftp = connect_to_ftp(ftp_host, ftp_username, ftp_password)

    # # Uploading datas from a local folder to FTP
    # upload_files_to_ftp(ftp, "temp\final_PNG\templates_v1\EN", remote_ftp_dir)

    # disconnect_from_ftp(ftp)
    
    # # Remove temporary directory after processing is complete
    # remove_local_directory(temp_folder)

    # Calculate execution time
    end_time = datetime.now()
    print(f"Execution time: {end_time - start_time}")

if __name__ == "__main__":

    main()
