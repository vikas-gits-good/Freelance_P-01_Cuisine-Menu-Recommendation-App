import os
import json
import pandas as pd
from logging import Logger
from typing import Any, Dict

from src.Logging.logger import log_etl
from src.Exception.exception import LogException, CustomException


def save_json(data: Dict[str, Any], save_path: str, log: Logger = log_etl):
    try:
        dir_path = os.path.dirname(save_path)
        os.makedirs(dir_path, exist_ok=True)
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        log.info("Successfully saved JSON data to file")

    except Exception as e:
        LogException(e, logger=log)
        # raise CustomException(e)


def read_json(save_path: str, log: Logger = log_etl) -> Dict[str, Any]:
    data = {"data": "error_reading_json"}
    try:
        with open(save_path, "w", encoding="utf-8") as f:
            data = json.load(f)
        log.info("Successfully read JSON data from file")

    except Exception as e:
        LogException(e, logger=log)
        # raise CustomException(e)

    return data


def save_dataframe(data: pd.DataFrame, save_path: str, log: Logger = log_etl):
    try:
        dir_path = os.path.dirname(save_path)
        os.makedirs(dir_path, exist_ok=True)
        data.to_pickle(path=save_path)
        log.info("Successfully saved DataFrame to file")

    except Exception as e:
        LogException(e, logger=log)
        # raise CustomException(e)


def read_dataframe(save_path: str, log: Logger = log_etl) -> pd.DataFrame:
    data = pd.DataFrame({"data": ["error_reading_dataframe"]})
    try:
        data = pd.read_pickle(save_path)
        log.info("Successfully read DataFrame from file")

    except Exception as e:
        LogException(e, logger=log)
        # raise CustomException(e)

    return data
