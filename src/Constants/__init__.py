from dataclasses import dataclass


@dataclass
class SwiggyConstats:
    DATABASE_NAME = "Swiggy_Data"
    COLLECTION_RESTAURANT_CONFIG = "01_Restaurant_Config"
    COLLECTION_SCRAPED_DATA = "02_Scraped_JSON"
    COLLECTION_RESTAURANT_MENU = "03_Restaurant_Menu_JSON"


@dataclass
class MongoDBConstants:
    CONNECTION_URI = (
        "mongodb://{username}:{password}@localhost:27017/mongodb-local?authSource=admin"
    )
    SWIGGY = SwiggyConstats()
