"""upload via API (ACTIVE)"""

import aiohttp
import asyncio
import logging
from pathlib import Path
import requests
import os


RED = "\033[91m"
GREEN = "\033[92m"
RESET = "\033[0m"


async def upload_results_async(
        config: dict, directories: dict, logger: logging.Logger
        ) -> None:
    """
    Orchestrates async upload of generated images via API
    """

    logger.info(f"Start uploading a final folder")
    uploaded = await upload_files_to_api_async(
                        base_url=config["clim4cast"]["base_url"],
                        username=config["clim4cast"]["username"],
                        password=config["clim4cast"]["password"],
                        root_folder=directories["folder_to_send"],
                        logger=logger,
                        )
    logger.info(f"Upload finished. Uploaded {len(uploaded)} files via API")


async def upload_files_to_api_async(
                        base_url: str,
                        username: str,
                        password: str,
                        root_folder: str,
                        logger: logging.Logger,
                        max_concurrent: int = 10,
                        ) -> list:
    """
    Recursively uploads all files from 'final/' tree to Clim4Cast API.

    Example valid paths:
        final/downloads/normal/CZ/AWP_0-40cm_0.png
        final/layers/reduced/UTCI_3.png
    """
    uploaded = []

    if not os.path.isdir(root_folder):
        logger.error(f" Root folder does not exist: {root_folder}")
        return uploaded
    
    root_folder = Path(root_folder)
    
    all_files = list(root_folder.rglob("*.*")) 

    auth = aiohttp.BasicAuth(username, password)

    connector = aiohttp.TCPConnector(
        limit=max_concurrent,
        limit_per_host=max_concurrent,
        ssl=False
    )

    timeout = aiohttp.ClientTimeout(total=300)

    semaphore = asyncio.Semaphore(max_concurrent)

    async with aiohttp.ClientSession(
        connector=connector,
        timeout=timeout,
        auth=auth,
    ) as session:
        
        tasks = [
            upload_single_file(
                session=session,
                file_path=file_path,
                root_path=root_folder,
                base_url=base_url,
                logger=logger,
                semaphore=semaphore,
            )
            for file_path in all_files
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for file_path, result in zip(all_files, results):
            if isinstance(result, Exception):
                logger.error(f"{RED}EXCEPTION {file_path}: {result}{RESET}")
            elif result:
                uploaded.append(file_path)
    
    return uploaded


async def upload_single_file(
        session: aiohttp.ClientSession,
        file_path: Path,
        root_path: Path,
        base_url: str,
        logger: logging.Logger,
        semaphore: asyncio.Semaphore,
) -> bool:
    """
    Uploads a single file to the API
    """
    async with semaphore:

        relative_path = file_path.relative_to(root_path).as_posix()
        url = f"{base_url.rstrip('/')}/upload/{relative_path}"

        try:
            async with session.post(url, data=file_path.read_bytes()) as response:
                if response.status == 200:
                    logger.info(f"{GREEN}OK status_code 200 {url}{RESET}")
                    return True
                else:
                    text = await response.text()
                    logger.error(
                        f"{RED}{file_path} -> {response.status}: {text}{RESET}"
                        )
                    return False
                
        except asyncio.TimeoutError:
            logger.error(f"{RED}TIMEOUT {file_path}{RESET}")
            return False
        except aiohttp.ClientError as err:
            logger.error(f"{RED}CLIENT ERROR {file_path}: {err}{RESET}")
            return False
        except Exception as err:
            logger.error(f"{RED}EXCEPTION {file_path}: {err}{RESET}")
            return False


def upload_files_to_api(
                        base_url: str,
                        username: str,
                        password: str,
                        root_folder: str,
                        logger: logging.Logger,
                        ) -> list:
    """
    Recursively uploads all files from 'final/' tree to Clim4Cast API.

    Example valid paths:
        final/downloads/normal/CZ/AWP_0-40cm_0.png
        final/layers/reduced/UTCI_3.png

    Args:
        base_url (str): Base API endpoint
        username (str): Username for Basic Auth
        password (str): Password for Basic Auth
        root_folder (str): Local root directory containing all files to upload

    Returns:
        list: A list of full local file paths that were successfully uploaded
    """
    uploaded = []

    if not os.path.isdir(root_folder):
        logger.error(f" Root folder does not exist: {root_folder}")
        return uploaded
    
    root_folder = Path(root_folder)
    all_files = list(root_folder.rglob("*.*")) 

    for current_file in all_files:

        relative_path = os.path.relpath(
            current_file, root_folder
            ).replace("\\", "/")
        url = f"{base_url.rstrip('/')}/upload/{relative_path}"

        try:
            with open(current_file, "rb") as f:
                res = requests.post(
                                    url,
                                    data=f,
                                    auth=(username, password),
                                    verify=False
                                    )

            if res.status_code == 200:
                logger.info(f"{GREEN} OK status_code 200 {url}{RESET}")
                uploaded.append(current_file)
            else:
                logger.error(f"{current_file} → {res.status_code}: {res.text}")

        except Exception as e:
            logger.error(f" EXCEPTION {current_file}: {e}")

    return uploaded


def upload_results(
        config: dict, directories: dict, logger: logging.Logger
        ) -> None:
    """
    Orchestrates upload of generated images via API
    """
    logger.info(f"Start uploading a final folder")
    uploaded = upload_files_to_api(
                        base_url=config["clim4cast"]["base_url"],
                        username=config["clim4cast"]["username"],
                        password=config["clim4cast"]["password"],
                        root_folder=directories["folder_to_send"],
                        logger=logger,
                        )
    logger.info(f"Upload finished. Uploaded {len(uploaded)} files via API")
