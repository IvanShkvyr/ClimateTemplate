import logging
import os
import sys


DEFAULT_LOG_LEVEL = "INFO"

LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

def setup_logger(log_name: str = "image_generation") -> logging.Logger:
    """
    Configurate and return a logger that logs message to a file and console.

    Parameters:
        log_name (str): log file name.

    Return:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(log_name)

    if logger.hasHandlers():
        return logger

    level_name = os.getenv("CLIM4CAST_LOG_LEVEL", DEFAULT_LOG_LEVEL).upper()
    level = LOG_LEVELS.get(level_name, logging.INFO)
    logger.setLevel(level)

    formatter = logging.Formatter(
        fmt=(
            "%(asctime)s - [%(levelname)s] - %(name)s"
            " - (%(filename)s:%(lineno)d) - %(message)s"
            ),
        datefmt="%Y-%m-%d %H:%M:%S",
        )

    #Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    # File handler
    log_file = os.getenv("CLIM4CAST_LOG_FILE")
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logger.propagate = False

    return logger


