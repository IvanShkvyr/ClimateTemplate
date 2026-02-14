import sys
import asyncio

sys.path.append('D:/CzechGlobe/Task/task_28_Clim4Cast_New_redaction/c4c_website/image-generation')

from src.data_loader import load_app_config, wait_for_input_data
from src.data_processor import generate_base_raster
from src.data_visualizer import generate_visualizations
from src.enviroment import prepere_enviroment, generate_templates, cleanup
from src.transport.api import upload_results_async
from src.logging_utils import setup_logger


async def main() -> None:
    """
    Main asynchronous pipeline for processing and uploading data
    """

    logger = setup_logger()
    logger.info(f"---------START--------")

    directories = None

    try:
        config = load_app_config()

        path_to_data = wait_for_input_data(config, logger)
        directories = prepere_enviroment(config, logger)

        list_img = generate_base_raster(
            path_to_data,
            config,
            directories,
            logger
            )
        visualizations = generate_visualizations(
                                config,
                                list_img,
                                directories,
                                logger
                                )
        generate_templates(config, visualizations, directories, logger)

        await upload_results_async(config, directories, logger)

        logger.info(f"Pipeline finished successfully.")

    except Exception as exc:
        logger.exception(f"Pipeline failed: {exc}")

    finally:
        if directories:
            cleanup(directories, logger)

        logger.info(f"---------FINISH--------")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())


