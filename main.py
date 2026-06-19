import sys
import asyncio

sys.path.append('D:/CzechGlobe/Task/task_28_Clim4Cast_New_redaction/c4c_website/image-generation')

from src.core.config import load_app_config
from src.core.logging_conf import setup_logger
from src.io.local_storage import (
                                    wait_for_input_data,
                                    prepare_environment,
                                    cleanup
                                    )
from src.io.transport.api import upload_results_async
from src.services.raster_processor import generate_base_raster
from src.services.visualizer import generate_visualizations
from src.services.template_engine import generate_templates


async def main() -> None:
    """
    Main asynchronous pipeline for processing and uploading data
    """

    logger = setup_logger()
    logger.info(f"--------- Pipeline Execution Started --------")

    try:
        config = load_app_config()

        # Waiting for data and preparing the environment
        path_to_data = wait_for_input_data(config, logger)
        prepare_environment(config, logger)

        # 1. Creating basic
        list_img = generate_base_raster(
            path_to_data,
            config,
            logger,
            )
        
        # 2. Creating vizualization (PNG files)
        visualizations = generate_visualizations(
                                config,
                                list_img,
                                logger
                                )

        # 3. Adding raster data to templates
        generate_templates(config, visualizations, logger)

        # 4. Uploading results asynchronously
        await upload_results_async(config, logger)

        logger.info(f"Pipeline finished successfully.")

    except Exception as exc:
        logger.exception(f"Pipeline failed: {exc}")

    finally:
        if config: 
            cleanup(config, logger)
            logger.info(f"Temporary directories cleaned up.")   

        logger.info(f"--------- Pipeline Execution Finished --------")


if __name__ == "__main__":
    asyncio.run(main())
