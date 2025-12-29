import os
from dotenv import load_dotenv
from dataclasses import dataclass
from src.Constants import MongoDBConstats


class MongoDBConfig:
    def __init__(self):
        load_dotenv("src/Secrets/mongodb.env")
        MONGO_USERNAME = os.getenv("MONGO_INITDB_ROOT_USERNAME")
        MONGO_PASSWORD = os.getenv("MONGO_INITDB_ROOT_PASSWORD")

        self.mndb_conn_uri = MongoDBConstats.CONNECTION_URI.format(
            username=MONGO_USERNAME,
            password=MONGO_PASSWORD,
        )

        @dataclass
        class swiggy:
            database = MongoDBConstats.swiggy_cnsts.DATABASE_NAME
            coll_sitemap = MongoDBConstats.swiggy_cnsts.COLLECTION_SITEMAP
            coll_rstn_cnfg = MongoDBConstats.swiggy_cnsts.COLLECION_RESTAURANT_CONFIG
            coll_rstn_menu = MongoDBConstats.swiggy_cnsts.COLLECTION_RESTAURANT_MENU
