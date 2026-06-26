import logging
import time
from typing import Callable, TypeVar


T = TypeVar("T")


def run_step(
        step_name: str,
        action: Callable[[], T],
        logger: logging.Logger
        ) -> T:
    """Run a single pipeline step with consistent start/end/duration logging."""
    logger.info(f"--- Step started: {step_name} ---")
    start = time.monotonic()
    try:
        result = action()
    except Exception:
        logger.exception(f"--- Step failed: {step_name} ---")
        raise
    duration = time.monotonic() - start
    logger.info(f"--- Step finished: {step_name} ({duration:.1f}s) ---")

    return result


async def run_step_async(step_name: str, action, logger: logging.Logger):
    """
    Run a single async pipeline step with consistent start/end/duration logging.
    """
    logger.info(f"--- Step started: {step_name} ---")
    start = time.monotonic()

    try:
        result = await action()
    except Exception:
        logger.exception(f"--- Step failed: {step_name} ---")
        raise
    duration = time.monotonic() - start
    logger.info(f"--- Step finished: {step_name} ({duration:.1f}s) ---")
    return result

