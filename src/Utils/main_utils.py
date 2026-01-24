import os
import json
import pandas as pd
from logging import Logger
from pymongo import MongoClient, UpdateOne, AsyncMongoClient

from typing import Any, Dict, List, Literal, Iterator, AsyncIterator

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
            if collection == db_config.swiggy.coll_rstn_cnfg:
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
                    # [{'rstn_id':123, 'config': {}},{'rstn_id':456, 'config': {}},...]
                    filter_query = {"rstn_id": rec["rstn_id"]}
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
    item: Literal["city", "rstn_id", "config"] = "rstn_id",
    prefix: Literal["Extraction", "Transformation", "Load"] = "Extraction",
    db_config: MongoDBConfig = MongoDBConfig(),
    log: Logger = log_etl,
) -> dict | list:
    try:
        log.info(f"{prefix}: Communicating with MongoDB: '{database}/{collection}'")
        mongo_client = MongoClient(db_config.mndb_conn_uri)
        colls = mongo_client[database][collection]
        # get data
        data = []  # list(colls.find())
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

        if collection == db_config.swiggy.coll_rstn_cnfg:
            colls.create_index("city", background=True)
            # clean_data= [{item["city"]: item["config"]} for item in data]
            for item in data:
                clean_data.update({item["city"]: item["config"]})

        elif collection == db_config.swiggy.coll_scrp_data:
            colls.create_index("rstn_id", background=True)
            cursor = colls.find({}, {item: 1, "_id": 0}, batch_size=1000)
            clean_data = [doc[item] for doc in cursor]
            log_etl.info(f"Extraction: Acquired {len(clean_data):,} {item}")

        elif collection == db_config.swiggy.coll_upst_fail:
            colls.create_index("rstn_id", background=True)
            cursor = colls.find({}, {item: 1, "_id": 0}, batch_size=1000)
            clean_data = [doc[item] for doc in cursor]
            log_etl.info(f"Extraction: Acquired {len(clean_data):,} {item}")

        return clean_data

    except Exception as e:
        LogException(e, logger=log)
        return {}


def read_cypher(
    save_path: str,
    chunk: bool = False,
    log: Logger = log_etl,
) -> str | List[str]:
    data = ""
    try:
        with open(save_path, mode="rt", encoding="utf-8", newline="\r\n") as f:
            data = f.read()
        data = (
            [part.strip() for part in data.split("\n\n") if part.strip()]
            if chunk
            else data
        )
        log.info("Successfully read Cypher code from file")

    except Exception as e:
        LogException(e, logger=log)
        # raise CustomException(e)

    return data


def fetch_batches(
    batch_size: int = 1024,
    limit: int = 0,
    db_config: MongoDBConfig = MongoDBConfig(),
    prefix: Literal["Extraction", "Transformation", "Load"] = "Load",
    log: Logger = log_etl,
) -> Iterator[List[Dict[str, Any]]]:
    try:
        database = db_config.swiggy.database
        collection = db_config.swiggy.coll_scrp_data

        log.info(f"{prefix}: Communicating with MongoDB: '{database}/{collection}'")
        with MongoClient(db_config.mndb_conn_uri) as mgcl:
            colls = mgcl[database][collection]
            cursor = colls.find(
                {}, {"_id": 0, "config": 1}, batch_size=batch_size
            ).limit(limit)  # limit=0 => no limits

            batch = []
            for doc in cursor:
                if "config" not in doc.keys():
                    continue

                batch.append(doc["config"])

                if len(batch) == batch_size:
                    log.info(f"{prefix}: Sending {batch_size:,} rows of data")
                    yield batch
                    batch = []

            if batch:
                log.info(f"{prefix}: Sending final {batch_size:,} rows of data")
                yield batch

            mgcl.close()

    except Exception as e:
        LogException(e, logger=log)
        # raise CustomException(e)


async def async_fetch_batches(
    batch_size: int = 1024,
    db_config: MongoDBConfig = MongoDBConfig(),
    prefix: Literal["Extraction", "Transformation", "Load"] = "Load",
    log: Logger = log_etl,
) -> AsyncIterator[List[Dict[str, Any]]]:
    try:
        database = db_config.swiggy.database
        collection = db_config.swiggy.coll_scrp_data

        log.info(f"{prefix}: Communicating with MongoDB: '{database}/{collection}'")
        async with AsyncMongoClient(db_config.mndb_conn_uri) as amgcl:
            colls = amgcl[database][collection]
            cursor = colls.find(
                {}, {"_id": 0, "config": 1}, batch_size=batch_size
            )  # .limit(20)  # limiting for test

            batch = []
            async for doc in cursor:
                if "config" not in doc.keys():
                    continue

                batch.append(doc["config"])

                if len(batch) == batch_size:
                    yield batch
                    batch = []

            if batch:
                yield batch

    except Exception as e:
        LogException(e, logger=log)
        # raise CustomException(e)


def format_time(seconds: float) -> str:
    """Format elapsed time as '00 hr, 00 min, 00 sec'."""
    hrs, rem = divmod(seconds, 3600)
    mins, secs = divmod(rem, 60)
    return f"{int(hrs):2d} hr, {int(mins):2d} min, {int(secs):2d} sec"
