import asyncio
import sys
from datetime import date

from clim4cast_imagegen.core.config import load_app_config
from clim4cast_imagegen.core.exceptions import Clim4CastError
from clim4cast_imagegen.core.logging_conf import setup_logger
from clim4cast_imagegen.core.pipeline import run_step, run_step_async
from clim4cast_imagegen.io.api import upload_results
from clim4cast_imagegen.io.local_storage import (
    cleanup,
    find_input_data,
    is_already_processed,
    mark_processed,
    prepare_environment,
)
from clim4cast_imagegen.services.raster_processor import generate_base_raster
from clim4cast_imagegen.services.template_engine import generate_templates
from clim4cast_imagegen.services.visualizer import generate_visualizations


async def main() -> None:
    """
    Run one full pipeline pass: generate images and upload them.
    """

    logger = setup_logger()
    logger.info("Pipeline Execution Started")
    config = None

    try:
        config = load_app_config()
        today = date.today()

        # Skip if today's data was already processed
        if is_already_processed(today):
            logger.info("Today's data already processed; nothing to do.")
            return

        # Skip if input data is not ready yet (timer will retry)
        path_to_data = find_input_data (config, logger)
        if path_to_data is None:
            logger.info("Exiting: input data not ready.")
            return

        prepare_environment(config, logger)

        # 1. Creating basic rasters
        list_img = run_step(
            "generate_base_raster",
            lambda: generate_base_raster(path_to_data, config, logger),
            logger)

        # 2. Creating visualization (PNG files)
        visualizations = run_step(
            "generate_visualizations",
            lambda: generate_visualizations(config, list_img, logger),
            logger,
            )

        # 3. Adding raster data to templates
        run_step(
            "generate_templates",
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
                "upload_results",
                lambda: upload_results(config, logger),
                logger,
            )

        logger.info("Pipeline finished successfully.")

        # Mark done ONLY after a real delivery (dry-run doesn't upload)
        if not config.dry_run:
            mark_processed(today)

        cleanup(config, logger)
        logger.info("Temporary directories cleaned up.")

    except Clim4CastError as exc:
        logger.error(str(exc))
        raise

    except Exception as exc:
        logger.exception(f"Pipeline failed: {exc}")
        raise

    finally:
        logger.info("Pipeline Execution Finished")

def run() -> None:
    """Run the pipeline once and exit with code 1 if it fails."""
    try:
        asyncio.run(main())
    except Exception:
        sys.exit(1)
