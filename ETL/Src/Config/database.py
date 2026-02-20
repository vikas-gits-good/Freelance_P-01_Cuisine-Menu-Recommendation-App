import os
from urllib.parse import quote

from dotenv import load_dotenv

from Src.Constants import FalkorDBConstants, MongoDBConstants, RedisDBConstants


class SwiggyConfig:
    def __init__(self):
        self.database = MongoDBConstants.SWIGGY.DATABASE_NAME
        self.coll_uq_ct_ids = MongoDBConstants.SWIGGY.COLLECTION_UNIQUE_CITY_IDS
        self.coll_uq_st_ids = MongoDBConstants.SWIGGY.COLLECTION_UNIQUE_STATE_IDS
        self.coll_uq_cr_ids = MongoDBConstants.SWIGGY.COLLECTION_UNIQUE_COUNTRY_IDS
        self.coll_ms_ct_nam = MongoDBConstants.SWIGGY.COLLECTION_MISS_CITY_NAMES
        self.coll_rstn_cnfg = MongoDBConstants.SWIGGY.COLLECTION_RESTAURANT_CONFIG
        self.coll_scrp_data = MongoDBConstants.SWIGGY.COLLECTION_SCRAPED_DATA
        self.coll_upst_fail = MongoDBConstants.SWIGGY.COLLECTION_UPSERT_FAIL


class MongoDBConfig:
    """Method to get credentials to connect to a MongoDB instance"""

    def __init__(self):
        load_dotenv(".env")
        self.conn_uri = MongoDBConstants.CONNECTION_URI.format(
            user=quote(str(os.getenv("ETL_MONGO_USER"))),
            pswd=quote(str(os.getenv("ETL_MONGO_PSWD"))),
            host=quote(str(os.getenv("ETL_MONGO_HOST"))),
            port=quote(str(os.getenv("ETL_MONGO_PORT"))),
            name=quote(str(os.getenv("ETL_MONGO_NAME"))),
        )
        self.swiggy = SwiggyConfig()


class RedisDBConfig:
    """Method to get credentials to connect to a RedisDB instance"""

    def __init__(self):
        load_dotenv(".env")
        REDIS_USER = os.getenv("ETL_REDIS_USER")
        REDIS_PSWD = os.getenv("ETL_REDIS_PSWD")
        REDIS_HOST = os.getenv("ETL_REDIS_HOST")
        REDIS_PORT = os.getenv("ETL_REDIS_PORT", "6379")

        def _get_data(database: int = 0):
            data_dict = {
                "username": REDIS_USER,
                "password": REDIS_PSWD,
                "host": str(REDIS_HOST),
                "port": int(REDIS_PORT),
                "db": database,
            }
            data_url = RedisDBConstants.CONNECTION_URI.format(
                user=quote(str(os.getenv("ETL_REDIS_USER"))),
                pswd=quote(str(os.getenv("ETL_REDIS_PSWD"))),
                host=quote(str(os.getenv("ETL_REDIS_HOST"))),
                port=quote(str(os.getenv("ETL_REDIS_PORT"))),
                daba=database,
            )
            return data_dict, data_url

        self.redis_dict_main, self.redis_url_main = _get_data(0)
        self.redis_dict_fail_1, self.redis_url_fail_1 = _get_data(1)
        self.redis_dict_fail_2, self.redis_url_fail_2 = _get_data(2)


class FalkorDBConfig:
    """Method to get credentials to connect to a FalkorDB instance"""

    def __init__(self):
        load_dotenv(".env")
        self.conn_uri = FalkorDBConstants.CONNECTION_URI.format(
            user=quote(str(os.getenv("ETL_FALKOR_USER"))),
            pswd=quote(str(os.getenv("ETL_FALKOR_PSWD"))),
            host=quote(str(os.getenv("ETL_FALKOR_HOST"))),
            port=quote(str(os.getenv("ETL_FALKOR_PORT"))),
        )
        self.conn_dict = {
            "username": str(os.getenv("ETL_FALKOR_USER")),
            "password": str(os.getenv("ETL_FALKOR_PSWD")),
            "host": str(os.getenv("ETL_FALKOR_HOST")),
            "port": int(os.getenv("ETL_FALKOR_PORT", "6379")),
        }
        self.fdb_kg = os.getenv("ETL_FALKOR_DABA", "PROD_KG")
