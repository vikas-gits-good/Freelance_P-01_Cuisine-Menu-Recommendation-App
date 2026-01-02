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
    data: dict | list[dict] | pd.DataFrame,
    database: str,
    collection: str,
    prefix: Literal["Extraction", "Transformation", "Load"] = "Extraction",
    db_config: MongoDBConfig = MongoDBConfig(),
    log: Logger = log_etl,
):
    try:
        log.info(f"{prefix}: Checking datatype and converting")
        record = data
        # if isinstance(data, dict):
        #     record = [data]

        # elif isinstance(data, List):
        #     record = data

        # elif isinstance(data, pd.DataFrame):
        #     record = df_to_json(data, log)

        log.info(f"{prefix}: Communicating with MongoDB: '{database}/{collection}'")
        mongo_client = MongoClient(db_config.mndb_conn_uri)
        colls = mongo_client[database][collection]

        log.info(f"{prefix}: Preparing data for upsert operations")

        operations = []

        if database == db_config.swiggy.database:
            if (
                collection == db_config.swiggy.coll_rstn_cnfg
                or collection == db_config.swiggy.coll_rstn_menu
            ):
                # Data format: {'city_1':{city_1_data},'city_2':{city_2_data}}
                for city_name, city_data in record.items():
                    filter_query = {"city": city_name}

                    # First, ensure the city document exists with base structure
                    colls.update_one(
                        filter_query,
                        {
                            "$setOnInsert": {
                                "city": city_name,
                                "config": {"restaurants": []},
                            }
                        },
                        upsert=True,
                    )

                    # Update city-level fields (everything except restaurants)
                    city_level_fields = {
                        k: v for k, v in city_data.items() if k != "restaurants"
                    }

                    if city_level_fields:
                        operations.append(
                            UpdateOne(
                                filter_query,
                                {
                                    "$set": {
                                        f"config.{k}": v
                                        for k, v in city_level_fields.items()
                                    }
                                },
                            )
                        )

                    # Now update individual restaurants by rstn_id
                    if "restaurants" in city_data:
                        for restaurant in city_data["restaurants"]:
                            rstn_id = restaurant.get("rstn_id")
                            if rstn_id:
                                # Filter for specific restaurant in the array
                                restaurant_filter = {
                                    "city": city_name,
                                    "config.restaurants.rstn_id": rstn_id,
                                }

                                # Check if restaurant exists in array
                                existing = colls.find_one(restaurant_filter)

                                if existing:
                                    # Update existing restaurant using positional operator
                                    operations.append(
                                        UpdateOne(
                                            restaurant_filter,
                                            {
                                                "$set": {
                                                    "config.restaurants.$": restaurant
                                                }
                                            },
                                        )
                                    )
                                else:
                                    # Add new restaurant to array
                                    operations.append(
                                        UpdateOne(
                                            filter_query,
                                            {
                                                "$push": {
                                                    "config.restaurants": restaurant
                                                }
                                            },
                                        )
                                    )

            elif collection == db_config.swiggy.coll_scrp_data:
                for rec in record:
                    restaurant_id = rec["data"]["cards"][2]["card"]["card"]["info"][
                        "id"
                    ]
                    rec["restaurant_id"] = restaurant_id  # restaurant id is unique
                    filter_query = {"restaurant_id": restaurant_id}
                    operations.append(
                        UpdateOne(filter_query, {"$set": rec}, upsert=True)
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
        # get data
        data = list(colls.find())
        """data = [
            {
                '_id': ObjectId('695238e68f4ca8f90d6caeef'), 
                'city': 'abohar', 
                'config': {
                    'name': 'Abohar, Abohar Tahsil, Fazilka, Punjab, 152116, India', 
                    'coords': [30.1450543, 74.1956597], 
                    'boundingbox': [...],
                    'address': {...},
                    'restaurants': [{},...],
                    'proxy': '...',
                }
            },
            ...
        ]
        """
        log.info(f"{prefix}: Restructuring data acquired from '{collection}'")
        clean_data = {}

        if (
            collection == db_config.swiggy.coll_rstn_cnfg
            or collection == db_config.swiggy.coll_rstn_menu
        ):
            for item in data:
                clean_data.update({item["city"]: item["config"]})

        elif collection == db_config.swiggy.coll_scrp_data:
            pass

        return clean_data

    except Exception as e:
        LogException(e, logger=log)
        return {}


def save_browser_session(
    log: Logger = log_etl,
):
    try:
        ...
        pass

    except Exception as e:
        LogException(e, logger=log)
        raise CustomException(e)
