import logging

DEFAULT_LOG_FILE = "logger.log"
DEFAULT_LEVEL = logging.DEBUG # logging.INFO logging.DEBUG

def setup_logger(
        log_file: str = DEFAULT_LOG_FILE,
        logger_level: int = DEFAULT_LEVEL,
        log_name: str = "image_generation",
        ) -> logging.Logger:
    """
    Configurate and return a logger that logs message to a file and console.

    Parameters:
        log_file (str): path to log file.
        logger_level (int): logging level.
        log_name (str): log file name.

    Return:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(log_name)

    if logger.hasHandlers():
        return logger

    logger.setLevel(logger_level)
    formatter = logging.Formatter(
        fmt=(
            "%(asctime)s - [%(levelname)s] - %(name)s"
            " - (%(filename)s:%(lineno)d) - %(message)s"
            ),
        datefmt="%Y-%m-%d %H:%M:%S",
        )

    #Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logger_level)
    console_handler.setFormatter(formatter)

    # File handler
    file_handler = logging.FileHandler(log_file, mode="a")
    file_handler.setLevel(logger_level)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    logger.propagate = False

    return logger


