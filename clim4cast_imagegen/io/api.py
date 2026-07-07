"""upload via API (ACTIVE)"""

import aiohttp
import asyncio
import logging
from pathlib import Path
import os

from clim4cast_imagegen.core.config import AppConfig


async def upload_results_async(
        config: AppConfig, logger: logging.Logger
        ) -> None:
    """
    Orchestrates async upload of generated images via API
    """

    logger.info(f"Start uploading a final folder")
    uploaded = await upload_files_to_api_async(
                        base_url=config.api.base_url,
                        username=config.api.username,
                        password=config.api.password,
                        root_folder=config.folders.to_send,
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
                logger.error(f"EXCEPTION {file_path}: {result}")
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
                    logger.info(f"OK status_code 200 {url}")
                    return True
                else:
                    text = await response.text()
                    logger.error(
                        f"{file_path} -> {response.status}: {text}"
                        )
                    return False
                
        except asyncio.TimeoutError:
            logger.error(f"TIMEOUT {file_path}")
            return False
        except aiohttp.ClientError as err:
            logger.error(f"CLIENT ERROR {file_path}: {err}")
            return False
        except Exception as err:
            logger.error(f"EXCEPTION {file_path}: {err}")
            return False
