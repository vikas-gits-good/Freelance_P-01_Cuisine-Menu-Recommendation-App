import json
import os
import re
from datetime import timedelta, timezone
from typing import Any, Dict, List, Literal, Optional

from dotenv import load_dotenv
from falkordb import FalkorDB
from pymongo import MongoClient, UpdateOne
from pymongo.cursor import Cursor
from redis import Redis

from Src.Config import FalkorDBConfig, MongoDBConfig, RedisDBConfig
from Src.Constants import MDBIndexKey

md_cnf = MongoDBConfig()
rd_cnf = RedisDBConfig()
fd_cnf = FalkorDBConfig()


def get_timezone() -> timezone:
    """Method to get timezone information from environment variables"""
    TZ = timezone(timedelta(hours=5, minutes=30))
    try:
        load_dotenv(".env")
        hrs, min = os.getenv("TIMEZONE", "5:30").split(":")
        TZ = timezone(timedelta(hours=int(hrs), minutes=int(min)))

    except Exception:
        pass  # fallback to default IST

    return TZ


def get_seeder_info() -> list[Any]:
    """Method to get Seeder function parameters from environment variables"""
    from .exception import LogException
    from .logger import log_etl

    try:
        load_dotenv(".env")
        website, pattern, headers, threads = [
            os.getenv(item, "")
            for item in [
                "SEEDER_WEBSITE",
                "SEEDER_PATTERN",
                "SEEDER_HEADERS",
                "SEEDER_THREADS",
            ]
        ]
        log_etl.info("Seeder: Got seeder ENV Vars")

    except Exception as e:
        LogException(e, logger=log_etl)

    return (website, re.compile(pattern), headers, int(threads), 10)


def read_json(path) -> Dict[str, Any]:
    """Method to read json data

    Args:
        path (str): Path to .json file
    """
    from .exception import LogException
    from .logger import log_etl

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        log_etl.info("Seeder: Read json data from file")

    except Exception as e:
        LogException(e, logger=log_etl)

    return data


COLLECTION_SCHEMA = {
    md_cnf.swiggy.coll_uq_ct_ids: ["uniq_city", "uniq_data"],
    md_cnf.swiggy.coll_uq_st_ids: ["uniq_state", "uniq_data"],
    md_cnf.swiggy.coll_uq_cr_ids: ["uniq_country", "uniq_data"],
    md_cnf.swiggy.coll_ms_ct_nam: ["uniq_city", "uniq_data"],
    md_cnf.swiggy.coll_rstn_cnfg: ["rstn_city", "rstn_data"],
    md_cnf.swiggy.coll_scrp_data: ["rstn_id", "rstn_city", "rstn_data"],
    md_cnf.swiggy.coll_upst_fail: ["rstn_id", "rstn_city", "rstn_data"],
}
UNIQ_COLLECTIONS = {
    md_cnf.swiggy.coll_uq_ct_ids,
    md_cnf.swiggy.coll_uq_st_ids,
    md_cnf.swiggy.coll_uq_cr_ids,
    md_cnf.swiggy.coll_ms_ct_nam,
}


def _transform_data(
    data: Dict[str, Dict[str, Any]] | List[Dict[str, Dict[str, Any]]],
    collection: str,
) -> List[Dict[str, Any]]:
    """Method to transform data into MongoDB upsertable form"""
    from .exception import LogException
    from .logger import log_etl

    try:
        if isinstance(data, list) and all(isinstance(item, dict) for item in data):
            records = data

        else:
            fields = COLLECTION_SCHEMA[collection]

            if collection in UNIQ_COLLECTIONS:
                records = [
                    {fields[0]: _idef, fields[1]: _data}
                    for _idef, _data in data.items()
                ]

            elif collection == md_cnf.swiggy.coll_rstn_cnfg:
                records = [
                    {fields[0]: _city, fields[1]: _data}
                    for _city, _data in data.items()
                ]

            elif collection == md_cnf.swiggy.coll_scrp_data:
                records = [
                    {fields[0]: rstn.ids, fields[1]: rstn.city_id, fields[2]: _data}
                    for rstn, _data in data.items()
                ]

            elif collection == md_cnf.swiggy.coll_upst_fail:
                records = [
                    {fields[0]: _id, fields[1]: _data.get("city", ""), fields[2]: _data}
                    for _id, _data in data.items()
                ]

            else:
                log_etl.info(f"Error: {collection}'s transformation isnt defined")
                records = None

    except Exception as e:
        LogException(e, logger=log_etl)
        records = None

    return records


def upsert_to_mongodb(
    data: Dict[str, Dict[str, Any]] | List[Dict[str, Dict[str, Any]]],
    database: str,
    collection: str,
    idx_key: MDBIndexKey = MDBIndexKey.RESTAURANT_ID,
    prefix: str = "Seeder",
) -> None:
    """Method to upsert seed urls to mongodb

    Args:
        data (Dict[str, Dict[str, Any]]): Seeded url data
        database (str): MongoDB database name
        collection (str): MongoDB collection name
        idx_key (str): search index column name
        prefix (str): Process name
    """
    from .exception import LogException
    from .logger import log_etl

    try:
        log_etl.info(f"{prefix}: Transforming data for upsertion")
        records = _transform_data(data, collection)
        if not records:  # Exit if error in _transform_data
            log_etl.info(f"{prefix}: Error transforming data, skipping data upsertion")
            return None

        log_etl.info(f"{prefix}: Communicating with '{database}/{collection}'")

        with MongoClient(md_cnf.conn_uri) as mgcl:  # auto close connection
            colls = mgcl[database][collection]
            operations = []

            for rec in records:
                try:
                    filter_query = {idx_key.value: rec[idx_key.value]}
                    operations.append(
                        UpdateOne(filter_query, {"$set": rec}, upsert=True)
                    )

                except Exception as e:
                    LogException(e, logger=log_etl)
                    continue

            if operations:
                log_etl.info(
                    f"{prefix}: Started upserting {len(operations):,} document(s) to '{database}/{collection}'"
                )
                colls.bulk_write(operations)
                log_etl.info(
                    f"{prefix}: Completed upserting {len(operations):,} document(s)"
                )

    except Exception as e:
        LogException(e, logger=log_etl)


def pull_from_mongodb(
    database: str,
    collection: str,
    idx_key: MDBIndexKey = MDBIndexKey.RESTAURANT_ID,
    city: Optional[str] = None,
    limit: int = 0,
    prefix: str = "Seeder",
) -> Dict[str, Any]:
    """Method to get seeded urls from mongodb

    Args:
        database (str): MongoDB database name
        collection (str): MongoDB collection name
        idx_key (MDBIndexKey): Search index column name
        city (Optional[str]): City urls to return. 'all' will return entire urls
        limit (int): Number of records to retrieve
        prefix (str): Process name
    """
    from .exception import LogException
    from .logger import log_etl

    try:
        log_etl.info(
            f"{prefix}: Preparing to communicate with '{database}/{collection}'"
        )
        key = idx_key.value.split("_")[0]

        with MongoClient(md_cnf.conn_uri) as mgcl:
            colls = mgcl[database][collection]
            colls.create_index(idx_key.value, background=True)
            cursor = colls.find({}, {"_id": 0}, batch_size=500).limit(limit)

            # I have set this up carefully.
            # Make sure the idx_key and city usage is correct.
            # Check Src/Expt/test_pull_from_mongodb.py
            pull_data = {}
            for doc in cursor:
                if (not city) or (city == "all") or (doc[idx_key] == city):
                    key_val = doc[idx_key]
                    data = doc[f"{key}_data"]
                    if key_val in pull_data:
                        if isinstance(data, list):
                            pull_data[key_val].extend(data)
                        else:
                            if isinstance(pull_data[key_val], list):
                                pull_data[key_val].append(data)
                            else:
                                pull_data[key_val].update(data)
                    else:
                        pull_data[key_val] = (
                            data
                            if collection
                            not in [
                                md_cnf.swiggy.coll_scrp_data,
                                md_cnf.swiggy.coll_upst_fail,
                            ]
                            else [data]
                        )

    except Exception as e:
        LogException(e, logger=log_etl)

    return pull_data


REDISDB_SCHEMA = {
    0: rd_cnf.redis_dict_main,
    1: rd_cnf.redis_dict_fail_1,
    2: rd_cnf.redis_dict_fail_2,
}


def upsert_to_redisdb(
    data: Dict[str, Any],
):
    """
    Method to upsert urls to redisdb for etl-scraper

    Args:
        data (Dict[str, Any]): Filtered data from MongoDB to upsert
    """
    from .exception import LogException
    from .logger import log_etl

    try:
        params = REDISDB_SCHEMA[0]
        log_etl.info("Seeder: Communicating with RedisDB")

        with Redis(**params, decode_responses=True) as rdcl:
            pipe = rdcl.pipeline()
            cmd_count = 0

            for rstn_city, rstn_data in data.items():
                try:
                    key = f"urls:{re.sub(' ', '-', rstn_city)}"
                    modf_data = [rstn["rstn_url"] for rstn in rstn_data["restaurants"]]
                    pipe.sadd(key, *modf_data)
                    cmd_count += 1

                    if cmd_count == 50:  # upsert every 50 cities
                        log_etl.info(
                            f"Seeder: Upserting {len(modf_data)} urls from '{key}' city"
                        )
                        pipe.execute()
                        cmd_count = 0

                except Exception as e:
                    LogException(e, logger=log_etl)
                    continue

            if cmd_count:
                log_etl.info(
                    f"Seeder: Upserting final {len(modf_data)} urls from '{key}' city"
                )
                pipe.execute()

    except Exception as e:
        LogException(e, logger=log_etl)


def get_urls_from_redis(
    key: str,
    batch_size: int = 100,
    database: Literal["0", "1", "2"] = "0",
    purpose: Literal["scrape", "update"] = "scrape",
    prefix: Literal["Extraction"] = "Extraction",
) -> List[str]:
    """Method to get urls to scrape in batches"""
    from .exception import LogException
    from .logger import log_etl

    try:
        params = REDISDB_SCHEMA[int(database)]

        log_etl.info(
            f"{prefix}: Getting urls list from Redis: 'redis/{database}/{key}'"
        )

        with Redis(**params, decode_responses=True) as rdcl:
            if purpose == "scrape":
                urls_list = rdcl.spop(name=key, count=batch_size)
                # dont use lpop, it doesnt work
            elif purpose == "update":
                urls_list = rdcl.smembers(name=key)

    except Exception as e:
        LogException(e, logger=log_etl)

    return urls_list


def put_urls_to_redis(
    key: str,
    data_list: List[str],
    database: Literal["0", "1", "2"] = "1",
    prefix: Literal["Extraction"] = "Extraction",
):
    """Method to return failed urls back to Redis Queue for scraping/storing"""
    from .exception import LogException
    from .logger import log_etl

    try:
        params = REDISDB_SCHEMA[int(database)]

        log_etl.info(f"{prefix}: Pushing data to Redis: 'redis/{database}/{key}'")

        with Redis(**params, decode_responses=True) as rdcl:
            rdcl.sadd(key, *data_list)  # dont use lpush, it duplicates

    except Exception as e:
        LogException(e, logger=log_etl)


def get_cities_from_redis(
    key: str = "urls:*",
    database: Literal["0", "1", "2"] = "0",
    prefix: str = "Extraction",
):
    """Method to get city names to iterate over while scraping"""
    from .exception import LogException
    from .logger import log_etl

    try:
        params = REDISDB_SCHEMA[int(database)]

        log_etl.info(f"{prefix}: Getting cities list from Redis: 'redis/{database}'")
        with Redis(**params, decode_responses=True) as rdcl:
            city_list = rdcl.keys(name=key)

    except Exception as e:
        LogException(e, logger=log_etl)

    return city_list
