"""upload via API (ACTIVE)"""

import aiohttp
import asyncio
from dataclasses import dataclass
import logging
from pathlib import Path
import os
from typing import List

from clim4cast_imagegen.core.config import AppConfig
from clim4cast_imagegen.core.exceptions import UploadIncompleteError


@dataclass(frozen=True)
class UploadReport:
    uploaded: List
    failed: List

    @property
    def total(self) -> int:
        return len(self.uploaded) + len(self.failed)



async def upload_results_async(
        config: AppConfig, logger: logging.Logger
        ) -> None:
    """
    Orchestrates async upload of generated images via API
    """

    logger.info(f"Start uploading a final folder")
    report = await upload_files_to_api_async(
                        base_url=config.api.base_url,
                        username=config.api.username,
                        password=config.api.password,
                        root_folder=config.folders.to_send,
                        logger=logger,
                        )
    logger.info(f"Delivered {len(report.uploaded)}/{report.total} files via API")

    if report.failed:
        raise UploadIncompleteError(report.failed)


async def upload_files_to_api_async(
                        base_url: str,
                        username: str,
                        password: str,
                        root_folder: str,
                        logger: logging.Logger,
                        max_concurrent: int = 10,
                        ) -> UploadReport:
    """
    Recursively uploads all files from 'final/' tree to Clim4Cast API.

    Example valid paths:
        final/downloads/normal/CZ/AWP_0-40cm_0.png
        final/layers/reduced/UTCI_3.png
    """
    if not os.path.isdir(root_folder):
        logger.error(f" Root folder does not exist: {root_folder}")
        return UploadReport(uploaded=[], failed=[])

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

        uploaded, failed = [], []

        for file_path, result in zip(all_files, results):
            if result is True:
                uploaded.append(file_path)
            else:
                failed.append(file_path)
                if isinstance(result, Exception):
                    logger.error(f"EXCEPTION {file_path}: {result}")

    return UploadReport(uploaded=uploaded, failed=failed)


async def upload_single_file(
        session: aiohttp.ClientSession,
        file_path: Path,
        root_path: Path,
        base_url: str,
        logger: logging.Logger,
        semaphore: asyncio.Semaphore,
        max_attempts: int = 3,
        base_delay: float = 1.0,
) -> bool:
    """
    Uploads a single file to the API
    """
    async with semaphore:

        relative_path = file_path.relative_to(root_path).as_posix()
        url = f"{base_url.rstrip('/')}/upload/{relative_path}"


        for attempt in range(1, max_attempts + 1):
            if attempt > 1:
                await asyncio.sleep(base_delay * 2 ** (attempt - 1))

            try:
                async with session.post(url, data=file_path.read_bytes()) as response:
                    if response.status == 200:
                        logger.info(f"OK status_code 200 {url}")
                        return True
                    elif 400 <= response.status < 500:
                        text = await response.text()
                        logger.error(
                            f"{file_path} -> {response.status}: {text} "
                            )
                        return False
                    elif response.status >= 500:
                        text = await response.text()
                        logger.warning(
                            f"{file_path} -> {response.status}: {text}, "
                            f"{attempt}/{max_attempts}"
                            )

            except (asyncio.TimeoutError, aiohttp.ClientError) as err:
                logger.warning(f"{file_path} {err}, {attempt}/{max_attempts}")

            except Exception as err:
                logger.error(f"EXCEPTION {file_path}: {err}")
                return False

        logger.error(f"failed after {max_attempts} attempts: {file_path}")
        return False
