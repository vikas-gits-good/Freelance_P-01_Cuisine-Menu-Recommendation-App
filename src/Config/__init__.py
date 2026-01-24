import os
from dotenv import load_dotenv
from src.Constants import MongoDBConstants


class SwiggyConfig:
    def __init__(self):
        self.database = MongoDBConstants.SWIGGY.DATABASE_NAME
        self.coll_rstn_cnfg = MongoDBConstants.SWIGGY.COLLECTION_RESTAURANT_CONFIG
        self.coll_scrp_data = MongoDBConstants.SWIGGY.COLLECTION_SCRAPED_DATA
        self.coll_upst_fail = MongoDBConstants.SWIGGY.COLLECTION_UPSERT_FAIL


class MongoDBConfig:
    def __init__(self):
        load_dotenv("src/Secrets/Database.env")
        MONGO_USER = os.getenv("MONGO_INITDB_ROOT_USERNAME")
        MONGO_PSWD = os.getenv("MONGO_INITDB_ROOT_PASSWORD")
        MONGO_HOST = os.getenv("MONGO_HOST")
        MONGO_PORT = os.getenv("MONGO_PORT")
        MONGO_NAME = os.getenv("MONGO_NAME")

        self.mndb_conn_uri = MongoDBConstants.CONNECTION_URI.format(
            user=MONGO_USER,
            pswd=MONGO_PSWD,
            host=MONGO_HOST,
            port=MONGO_PORT,
            name=MONGO_NAME,
        )
        self.swiggy = SwiggyConfig()
