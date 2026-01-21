from glob import glob
from enum import Enum
from dataclasses import dataclass


@dataclass
class ETLCyphersConstants:
    ALL_CYPHER_FILE_PATHS = glob("src/ETL/Cyphers/*.cyp")
    KNOWLEDGE_GRAPH_NAME = "Swiggy_KG"


@dataclass
class LocationConstants:
    LOCATION_DATA_FILE_PATHS = glob("src/ETL/Data/unq_ids_*.json")


class NodeLabels(str, Enum):  # do not reorder Location Enums
    COUNTRY = "Country"
    STATE = "State"
    CITY = "City"
    AREA = "Area"
    LOCALITY = "Locality"
    # ------------------- #
    RESTAURANT = "Restaurant"
    SUBCUISINE = "SubCuisine"
    MAINCUISINE = "MainCuisine"
    # ------------------- #
    MENU = "Menu"


class RelationshipLabels(str, Enum):
    HAS_STATE = "HAS_STATE"
    HAS_CITY = "HAS_CITY"
    HAS_AREA = "HAS_AREA"
    HAS_LOCALITY = "HAS_LOCALITY"
    # ------------------- #
    HAS_RESTAURANT = "HAS_RESTAURANT"
    SERVES_SUB_CUISINE = "SERVES_SUB_CUISINE"
    SERVES_MAIN_CUISINE = "SERVES_MAIN_CUISINE"
    # ------------------- #
    HAS_MENU = "HAS_MENU"


class IndexName(str, Enum):
    COUNTRY_ID = "country_ids_index"
    STATE_ID = "state_ids_index"
    CITY_ID = "city_ids_index"
    AREA_ID = "area_ids_index"
    LOCALITY_ID = "locality_ids_index"
    # ------------------- #
    COUNTRY_NAME = "country_name_index"
    STATE_NAME = "state_name_index"
    CITY_NAME = "city_name_index"
    AREA_NAME = "area_name_index"
    LOCALITY_NAME = "locality_name_index"
    # ------------------- #
    RESTAURANT_ID = "restaurant_ids_index"
    SUBCUISINE_ID = "subcuisine_ids_index"
    MAINCUISINE_ID = "maincuisine_ids_index"
    # ------------------- #
    RESTAURANT_NAME = "restaurant_name_index"
    SUBCUISINE_NAME = "subcuisine_name_index"
    MAINCUISINE_NAME = "maincuisine_name_index"
    # ------------------- #
    MENU_NAME = "menu_name_index"
