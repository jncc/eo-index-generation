import os
import logging
import sys


def get_size(path):
    # https://stackoverflow.com/questions/6080477/how-to-get-the-size-of-tar-gz-in-mb-file-in-python
    size = os.path.getsize(path)
    if size < 1024:
        return f"{size} bytes"
    elif size < 1024 ** 2:
        return f"{round(size/1024, 2)} KB"
    elif size < 1024 ** 3:
        return f"{round(size/(1024 ** 2), 2)} MB"
    elif size < 1024 ** 4:
        return f"{round(size/(1024 ** 3), 2)} GB"


def get_logger(name: str):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.hasHandlers():
        logger.addHandler(logging.StreamHandler(sys.stdout))

    return logger
