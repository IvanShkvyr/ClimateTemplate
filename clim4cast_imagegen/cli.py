import asyncio
import sys

from clim4cast_imagegen.core.config import load_app_config
from clim4cast_imagegen.core.logging_conf import setup_logger
from clim4cast_imagegen.io.local_storage import (
                                    wait_for_input_data,
                                    prepare_environment,
                                    cleanup
                                    )
from clim4cast_imagegen.io.api import upload_results_async
from clim4cast_imagegen.services.raster_processor import generate_base_raster
from clim4cast_imagegen.services.visualizer import generate_visualizations
from clim4cast_imagegen.services.template_engine import generate_templates
from clim4cast_imagegen.core.pipeline import run_step, run_step_async
from clim4cast_imagegen.core.exceptions import Clim4CastError



async def main() -> None:
    """
    Main asynchronous pipeline for processing and uploading data
    """

    logger = setup_logger()
    logger.info(f"--------- Pipeline Execution Started --------")
    config = None

    try:
        config = load_app_config()

        # Waiting for data and preparing the environment
        path_to_data = wait_for_input_data(config, logger)
        prepare_environment(config, logger)

        # 1. Creating basic
        list_img = run_step(
            "generate_base_raster",
            lambda: generate_base_raster(path_to_data, config, logger),
            logger)
        
        # 2. Creating vizualization (PNG files)
        visualizations = run_step(
            "creating_vizualization",
            lambda: generate_visualizations(config, list_img, logger),
            logger,
            )

        # 3. Adding raster data to templates
        run_step(
            "Adding_raster_data_to_templates",
            lambda: generate_templates(config, visualizations, logger),
            logger)

        # 4. Uploading results asynchronously
        if config.dry_run:
            logger.info(
                "DRY-RUN: skipping upload "
                "(set CLIM4CAST_DRY_RUN=False to enable real upload)"
            )
        else:
            await run_step_async(
                "upload_results_async",
                lambda: upload_results_async(config, logger),
                logger,
            )

        logger.info(f"Pipeline finished successfully.")
        cleanup(config, logger)
        logger.info(f"Temporary directories cleaned up.")

    except Clim4CastError as exc:
        logger.error(str(exc))
        raise

    except Exception as exc:
        logger.exception(f"Pipeline failed: {exc}")
        raise

    finally:
        logger.info(f"--------- Pipeline Execution Finished --------")

def run() -> None:
    """Synchronous entry point: runs the async pipeline once."""
    try:
        asyncio.run(main())
    except Exception:
        sys.exit(1)
