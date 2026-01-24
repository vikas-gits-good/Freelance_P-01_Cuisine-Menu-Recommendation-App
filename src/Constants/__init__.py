from dataclasses import dataclass


@dataclass
class SwiggyConstants:
    DATABASE_NAME = "Swiggy_Data"
    COLLECTION_RESTAURANT_CONFIG = "01_Restaurant_Config"
    COLLECTION_SCRAPED_DATA = "02_Scraped_JSON"
    COLLECTION_UPSERT_FAIL = "03_Upsert_Fail"


@dataclass
class MongoDBConstants:
    CONNECTION_URI = "mongodb://{user}:{pswd}@{host}:{port}/{name}?authSource=admin"
    SWIGGY = SwiggyConstants()
