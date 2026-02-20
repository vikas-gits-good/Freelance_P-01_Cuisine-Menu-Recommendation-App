import logging
import os
import sys
from datetime import datetime
from typing import Literal

from .utils import util_func

TZ = util_func.get_timezone()
logging.Formatter.converter = lambda *args: datetime.now(TZ).timetuple()


def get_tz_timestamp():
    """Always returns current TZ timestamp for filenames"""
    return datetime.now(TZ).strftime("%Y-%m-%d_%H-%M-%S")


def get_logger(log_type: Literal["full", "train", "pred", "etl", "flask"] = "etl"):
    log_dirs = {
        "etl": os.path.join(os.getcwd(), "logs", "etl"),
    }
    log_dir = log_dirs.get(log_type)
    if not log_dir:
        raise ValueError(f"Invalid log_type: {log_type}")

    os.makedirs(log_dir, exist_ok=True)
    timestamp = get_tz_timestamp()
    filename = f"{timestamp}_{log_type}.log"
    log_path = os.path.join(log_dir, filename)

    logger = logging.getLogger(f"{log_type}_logger")
    logger.setLevel(logging.INFO)

    # Prevent multiple handlers
    if not logger.handlers:
        fh = logging.FileHandler(log_path)
        fh.setLevel(logging.INFO)

        class CustomFormatter(logging.Formatter):
            def format(self, record):
                digits = 4
                record.lineno = f"{record.lineno:0{digits}}"
                return super().format(record)

        # SAME FORMAT for both file and stdout
        formatter = CustomFormatter(
            "[%(asctime)s] %(lineno)s %(name)s - %(levelname)s - %(message)s"
        )

        fh.setFormatter(formatter)
        logger.addHandler(fh)
        fh.flush()

        if os.getenv("LOG_TO_STDOUT", "1") == "1":
            sh = logging.StreamHandler(sys.stdout)
            sh.setLevel(logging.INFO)
            sh.setFormatter(formatter)
            logger.addHandler(sh)

    return logger


log_etl = get_logger("etl")
