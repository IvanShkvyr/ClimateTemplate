import logging

path_to_log_file = "logger.log"
logger_level = logging.DEBUG # logging.INFO logging.DEBUG

def setup_logger(
        log_file: str = path_to_log_file,
        logger_level: int = logger_level,
        log_name: str = "image_generation",
        ) -> logging.Logger:
    """
    Configurate and return a logger that logs message to a file and console.

    Parameters:
        log_file (str): path to log file.
        logger_lavel (int): logging level.
        log_name (str): log file name.

    Return:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(log_name)
    logger.setLevel(logger_level)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

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

    return logger
