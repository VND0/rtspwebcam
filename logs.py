import logging
import sys


def setup_logger(log_filename: str, loglevel: int) -> logging.Logger:
    logger = logging.getLogger()
    logger.setLevel(loglevel)

    formatter = logging.Formatter("%(levelname)s %(asctime)s: %(message) [File: %(filename)s; Line: %(lineno)s]",
                                  datefmt="%Y-%m-%d %H:%M:%S")
    file_handler = logging.FileHandler(filename=log_filename, mode="w", encoding="utf-8")
    stdout_handler = logging.StreamHandler(sys.stdin)

    file_handler.setFormatter(formatter)
    stdout_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stdout_handler)

    return logger
