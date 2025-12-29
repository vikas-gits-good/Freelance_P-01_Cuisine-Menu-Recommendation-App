import os
from dotenv import load_dotenv
from src.Constants import MongoDBConstants


class SwiggyConfig:
    def __init__(self):
        self.database = MongoDBConstants.SWIGGY.DATABASE_NAME
        self.coll_rstn_cnfg = MongoDBConstants.SWIGGY.COLLECTION_RESTAURANT_CONFIG
        self.coll_scrp_data = MongoDBConstants.SWIGGY.COLLECTION_SCRAPED_DATA
        self.coll_rstn_menu = MongoDBConstants.SWIGGY.COLLECTION_RESTAURANT_MENU


class MongoDBConfig:
    def __init__(self):
        load_dotenv("src/Secrets/mongodb.env")
        MONGO_USERNAME = os.getenv("MONGO_INITDB_ROOT_USERNAME")
        MONGO_PASSWORD = os.getenv("MONGO_INITDB_ROOT_PASSWORD")

        self.mndb_conn_uri = MongoDBConstants.CONNECTION_URI.format(
            username=MONGO_USERNAME,
            password=MONGO_PASSWORD,
        )
        self.swiggy = SwiggyConfig()
