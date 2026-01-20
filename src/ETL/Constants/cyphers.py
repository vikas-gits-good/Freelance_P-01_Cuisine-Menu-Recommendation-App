from glob import glob
from enum import Enum
from dataclasses import dataclass


@dataclass
class ETLCyphersConstants:
    ALL_CYPHER_FILE_PATHS = glob("src/ETL/Cyphers/*.cyp")
    KNOWLEDGE_GRAPH_NAME = "Swiggy_KG"


@dataclass
class LocationConstants:
    LOCATION_DATA_FILE_PATHS = glob("src/ETL/Data/sitemap/backups/unq_ids_*.json")


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
    MENU = "Menu"


class RelationshipTypes(str, Enum):
    HAS_STATE = "HAS_STATE"
    HAS_CITY = "HAS_CITY"
    HAS_AREA = "HAS_AREA"
    HAS_LOCALITY = "HAS_LOCALITY"
    HAS_RESTAURANT = "HAS_RESTAURANT"
    SERVES_SUB_CUISINE = "SERVES_SUB_CUISINE"
    SERVES_MAIN_CUISINE = "SERVES_MAIN_CUISINE"
    HAS_MENU = "HAS_MENU"
