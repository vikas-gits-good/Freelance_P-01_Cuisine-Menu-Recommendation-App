from dataclasses import dataclass
from src.Utils.main_utils import read_json
from random import random


@dataclass
class SwiggyRestaurantConstants:
    SWIGGY_API_ENDPOINT = "https://www.swiggy.com/dapi/restaurants/search/v3?lat={latitude}&lng={longitude}&str={query}&submitAction=ENTER"
    SWIGGY_MENU_ENDPOINT = "https://www.swiggy.com/dapi/menu/pl?page-type=REGULAR_MENU&complete-menu=true&lat={latitude}&lng={longitude}&restaurantId={rstrnID}&submitAction=ENTER"
    JSON_FILE_SAVE_PATH = "src/ETL/ETL_Data/json_data.json"
    DF_FILE_SAVE_PATH = "src/ETL/ETL_Data/df_data.pkl"
    COORDINATES_JSON = read_json(save_path="src/ETL/ETL_Constants/coordinates.json")
    DISTANCE = int(10 * (1 + random()))
    QUERIES = [
        f"All eateries within {DISTANCE}km range",
        f"Nearby restaurants in {DISTANCE}km",
        f"Restaurants {DISTANCE}km radius around",
        f"Dining spots in {DISTANCE}km circle",
        f"All food joints {DISTANCE}km nearby",
        f"Eateries within {DISTANCE}km distance",
        f"{DISTANCE}km radius all restaurants",
        f"Local restaurants {DISTANCE}km area",
        f"Food places in {DISTANCE}km",
        f"All dining {DISTANCE}km vicinity",
        f"Restaurants near me {DISTANCE}km",
        f"{DISTANCE}km all food outlets",
        f"Nearby eateries {DISTANCE}km radius",
        f"Dining options {DISTANCE}km range",
        f"All restaurants within {DISTANCE}km",
        f"Food spots {DISTANCE}km circle",
        f"{DISTANCE}km nearby all eateries",
        f"Restaurants in {DISTANCE}km zone",
        f"Local dining {DISTANCE}km radius",
        f"All food venues {DISTANCE}km",
    ]


@dataclass
class SwiggyLinksConstants:
    SWIGGY_SITEMAP_URL = "https://www.swiggy.com/sitemap.xml.gz"
    SWIGGY_SITEMAP_SCRAPE_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.swiggy.com/",
        "Accept": "application/json",
        "X-Requested-With": "XMLHttpRequest",
    }
    SITEMAP_GZIP_SAVE_DIRECTORY = "src/ETL/ETL_Data/sitemap"
    SITEMAP_JSON_SITEMAP_SAVE_DIRECTORY = "src/ETL/ETL_Data/sitemap/"
    SITEMAP_JSON_CITIES_SAVE_DIRECTORY = "src/ETL/ETL_Data/sitemap/"
    SITEMAP_JSON_RESTAURANTS_SAVE_DIRECTORY = "src/ETL/ETL_Data/sitemap/"
    JSON_SITEMAP_DATA_FILE_NAME = "sitemap_urls.json"
    JSON_CITIES_DATA_FILE_NAME = "unique_cities.json"
    JSON_RESTAURANTS_DATA_FILE_NAME = "unique_restaurants.json"


@dataclass
class NominatimOSMConstants:
    API_ENDPOINT = "https://nominatim.openstreetmap.org/search"
    SCRAPE_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
