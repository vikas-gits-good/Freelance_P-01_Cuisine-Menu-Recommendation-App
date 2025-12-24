from dataclasses import dataclass
from src.Utils.main_utils import read_json
from random import random


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
    JSON_SITEMAP_DATA_FILE_NAME = "sitemap_urls.json"  # All 3.2M+ urls

    UNIQUE_DATA_SAVE_DIRECTORY = "src/ETL/ETL_Data/sitemap/"
    UNIQUE_DATA_FILE_NAME = "unique_data.json"  # Filtered 0.47M+ restaurant urls


@dataclass
class NominatimOSMConstants:
    API_ENDPOINT = "https://nominatim.openstreetmap.org/search?q={query}&format=jsonv2&addressdetails=1&limit=1"
    SCRAPE_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    RATE_LIMIT = 1.2
    UNIQUE_DATA_SAVE_DIRECTORY = "src/ETL/ETL_Data/sitemap/"
    UNIQUE_DATA_FILE_NAME = "city_rstn_coords_data.json"


@dataclass
class RestaurantConstants:
    RESTAURANT_MENU_ENDPOINT = "https://www.swiggy.com/dapi/menu/pl?page-type=REGULAR_MENU&complete-menu=true&lat={latitude}&lng={longitude}&restaurantId={rstnID}&submitAction=ENTER"
    UNIQUE_DATA_SAVE_DIRECTORY = "src/ETL/ETL_Data/sitemap/"
    UNIQUE_DATA_FILE_NAME = "final_menu_data.json"
