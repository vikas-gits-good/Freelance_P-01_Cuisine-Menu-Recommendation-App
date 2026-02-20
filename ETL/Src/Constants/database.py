from dataclasses import dataclass
from enum import Enum


@dataclass
class SwiggyConstants:
    DATABASE_NAME = "Swiggy_Data"
    COLLECTION_UNIQUE_CITY_IDS = "00_UNQ_CITY_IDS"
    COLLECTION_UNIQUE_STATE_IDS = "00_UNQ_STATE_IDS"
    COLLECTION_UNIQUE_COUNTRY_IDS = "00_UNQ_COUNTRY_IDS"
    COLLECTION_MISS_CITY_NAMES = "00_MISS_CITY_NAMES"
    COLLECTION_RESTAURANT_CONFIG = "01_Restaurant_Config"
    COLLECTION_SCRAPED_DATA = "02_Scraped_JSON"
    COLLECTION_UPSERT_FAIL = "03_Upsert_Fail"


@dataclass
class MongoDBConstants:
    CONNECTION_URI = "mongodb://{user}:{pswd}@{host}:{port}/{name}?authSource=admin"
    SWIGGY = SwiggyConstants()


@dataclass
class RedisDBConstants:
    CONNECTION_URI = "redis://{user}:{pswd}@{host}:{port}/{daba}"


@dataclass
class FalkorDBConstants:
    CONNECTION_URI = "falkor://{user}:{pswd}@{host}:{port}"


class MDBIndexKey(str, Enum):
    UNIQUE_CITY = "uniq_city"
    UNIQUE_STATE = "uniq_state"
    UNIQUE_COUNTRY = "uniq_country"
    RESTAURANT_CITY = "rstn_city"
    RESTAURANT_ID = "rstn_id"
