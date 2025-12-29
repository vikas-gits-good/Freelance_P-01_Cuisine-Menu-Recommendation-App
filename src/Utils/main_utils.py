import os
import json
import pandas as pd
from logging import Logger
from pymongo import MongoClient, UpdateOne
from typing import Any, Dict, List, Literal

from src.Config import MongoDBConfig
from src.Logging.logger import log_etl
from src.Exception.exception import LogException, CustomException


def save_json(
    data: Dict[str, Any] | List[Dict[str, Any]], save_path: str, log: Logger = log_etl
):
    try:
        dir_path = os.path.dirname(save_path)
        os.makedirs(dir_path, exist_ok=True)
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        log.info("Successfully saved JSON data to file")

    except Exception as e:
        LogException(e, logger=log)
        # raise CustomException(e)


def read_json(save_path: str, log: Logger = log_etl) -> Dict[str, Any]:
    data = {"data": "error_reading_json"}
    try:
        with open(save_path, "r", encoding="utf-8") as f:
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


def df_to_json(data: pd.DataFrame, log: Logger):
    try:
        df = data.copy()
        df.reset_index(drop=True, inplace=True)
        records = list(json.loads(df.T.to_json()).values())
        return records

    except Exception as e:
        LogException(e, logger=log)
        # raise CustomException(e)


def upsert_to_mongodb(
    data: dict | pd.DataFrame,
    database: str,
    collection: str,
    prefix: Literal["Extraction", "Transformation", "Load"] = "Extraction",
    db_config: MongoDBConfig = MongoDBConfig(),
    log: Logger = log_etl,
):
    try:
        log.info(f"{prefix}: Checking datatype and converting")
        if isinstance(data, dict):
            record = data

        elif isinstance(data, pd.DataFrame):
            record = df_to_json(data, log)

        log.info(f"{prefix}: Communicating with MongoDB: '{database}/{collection}'")
        mongo_client = MongoClient(db_config.mndb_conn_uri)
        colls = mongo_client[database][collection]

        log.info(f"{prefix}: Preparing data for upsert operations")

        operations = []

        if database == "Swiggy_Data":
            if collection == "01_Restaurant_Config":
                ## Data format: {'city_1':{city_1_data},'city_2':{city_2_data}}
                for city_name, city_data in record.items():
                    filter_query = {"city": city_name}
                    document = {"city": city_name, "config": city_data}
                    operations.append(
                        UpdateOne(filter_query, {"$set": document}, upsert=True)
                    )

            elif collection == "02_Scraped_JSON":
                restaurant_id = record["data"]["cards"][2]["card"]["card"]["info"]["id"]
                record["restaurant_id"] = restaurant_id  # restaurant id is unique
                filter_query = {"restaurant_id": restaurant_id}
                operations.append(
                    UpdateOne(filter_query, {"$set": record}, upsert=True)
                )

            elif collection == "03_Restaurant_Menu_JSON":
                ## Data format: {'city_1':{city_1_data},'city_2':{city_2_data}}
                for city_name, city_data in record.items():
                    filter_query = {"city": city_name}
                    document = {"city": city_name, "config": city_data}
                    operations.append(
                        UpdateOne(filter_query, {"$set": document}, upsert=True)
                    )

        if operations:
            log.info(
                f"{prefix}: Started upserting {len(operations):,} document(s) to '{database}/{collection}'"
            )
            colls.bulk_write(operations)
            log.info(f"{prefix}: Completed upserting {len(operations):,} document(s)")

    except Exception as e:
        LogException(e, logger=log)
        # raise CustomException(e)


def get_from_mongodb(
    database: str,
    collection: str,
    prefix: Literal["Extraction", "Transformation", "Load"] = "Extraction",
    db_config: MongoDBConfig = MongoDBConfig(),
    log: Logger = log_etl,
) -> dict | pd.DataFrame:
    try:
        log.info(f"{prefix}: Communicating with MongoDB: '{database}/{collection}'")
        mongo_client = MongoClient(db_config.mndb_conn_uri)
        colls = mongo_client[database][collection]
        return {}

    except Exception as e:
        LogException(e, logger=log)
        return {}
