import logging
import logging.handlers
import sys


def setup_logger(log_filename: str, loglevel: int) -> logging.Logger:
    logger = logging.getLogger()
    logger.setLevel(loglevel)

    formatter = logging.Formatter("%(levelname)s %(asctime)s: %(message)s [File: %(filename)s; Line: %(lineno)s]",
                                  datefmt="%Y-%m-%d %H:%M:%S")

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    logger.addHandler(stdout_handler)

    file_handler = logging.handlers.RotatingFileHandler(filename=log_filename, mode="w", encoding="utf-8",
                                                        maxBytes=10 * 1024 * 1024, backupCount=1)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
