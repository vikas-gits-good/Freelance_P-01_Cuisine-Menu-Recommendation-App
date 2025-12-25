import os
from dotenv import load_dotenv
from typing import Literal, List, Dict, Any
from pydantic import BaseModel, model_validator

from crawl4ai.cache_context import CacheMode
from crawl4ai.components.crawler_monitor import CrawlerMonitor
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.proxy_strategy import RoundRobinProxyStrategy, ProxyConfig
from crawl4ai.async_dispatcher import RateLimiter, MemoryAdaptiveDispatcher
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from crawl4ai.browser_adapter import UndetectedAdapter
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
from src.ETL.ETL_Constants import (
    SwiggyLinksConstants,
    NominatimOSMConstants,
    RestaurantConstants,
)


# For processing sitemaps
class LinksConfig:
    def __init__(self) -> None:
        self.dir_path = SwiggyLinksConstants.SITEMAP_GZIP_SAVE_DIRECTORY
        self.save_path = SwiggyLinksConstants.SITEMAP_JSON_SITEMAP_SAVE_DIRECTORY
        os.makedirs(self.dir_path, exist_ok=True)
        self.main_link = SwiggyLinksConstants.SWIGGY_SITEMAP_URL
        self.headers = SwiggyLinksConstants.SWIGGY_SITEMAP_SCRAPE_HEADERS
        self.all_urls_file_path = os.path.join(
            SwiggyLinksConstants.SITEMAP_JSON_SITEMAP_SAVE_DIRECTORY,
            SwiggyLinksConstants.JSON_SITEMAP_DATA_FILE_NAME,
        )
        self.unique_data_file_path = os.path.join(
            SwiggyLinksConstants.UNIQUE_DATA_SAVE_DIRECTORY,
            SwiggyLinksConstants.UNIQUE_DATA_FILE_NAME,
        )

    def get_path(self, link: str) -> str:
        return os.path.join(self.dir_path, link.split("/")[-1])


# To get coordinates for Menu API calls
class CoordsConfig:
    def __init__(self) -> None:
        self.read_unique_data_path = os.path.join(
            SwiggyLinksConstants.UNIQUE_DATA_SAVE_DIRECTORY,
            SwiggyLinksConstants.UNIQUE_DATA_FILE_NAME,
        )
        self.save_unique_data_path = os.path.join(
            NominatimOSMConstants.UNIQUE_DATA_SAVE_DIRECTORY,
            NominatimOSMConstants.UNIQUE_DATA_FILE_NAME,
        )
        self.request_params = {
            "url": NominatimOSMConstants.API_ENDPOINT,
            "headers": NominatimOSMConstants.SCRAPE_HEADERS,
            "timeout": 20,
        }
        self.rtlm = NominatimOSMConstants.RATE_LIMIT


class RestaurantConfig:
    def __init__(self) -> None:
        self.read_unique_data_path = os.path.join(
            # NominatimOSMConstants.UNIQUE_DATA_SAVE_DIRECTORY,
            # NominatimOSMConstants.UNIQUE_DATA_FILE_NAME,
            "src/Research/sample_menus",
            "1_sample_rstn_data.json",
        )
        self.save_json_data_path = os.path.join(
            # RestaurantConstants.UNIQUE_DATA_SAVE_DIRECTORY,
            # '2_sample_scrp_data.json',
            "src/Research/sample_menus",
            "2_sample_scrp_data.json",
        )
        self.save_unique_data_path = os.path.join(
            # RestaurantConstants.UNIQUE_DATA_SAVE_DIRECTORY,
            # RestaurantConstants.UNIQUE_DATA_FILE_NAME,
            "src/Research/sample_menus",
            "3_sample_menu_data.json",
        )
        self.menu_api_ep = RestaurantConstants.RESTAURANT_MENU_ENDPOINT


# Restaurant details to scrape from json
class Restaurant(BaseModel):
    """pydantic.BaseModel that returns restaurant details from scraped JSON.

    Usage:
    ```python
    >>> rstn_data = scraped_json['data']
    >>> rstn = Restaurant(**rstn_data)
    >>> rstn
    >>> Restaurant(rstn_id=8840, rstn_name='Smoke House Deli', rstn_city='Delhi', rstn_locality='Saket', rstn_area='Saket', rstn_cuisines=['Pizzas', 'Pastas'], rstn_rating=4.2, rstn_address='...')
    ```
    Attributes:
        rstn_id (int): Unique ID for each restaurants. There are > 0.47M IDs in total.
        rstn_name (str): Restaurant name.
        rstn_city (str): City location of restaurant.
        rstn_locality (str): Locality of restaurant.
        rstn_area (str): Area if restaurant.
        rstn_cuisines (List['str']): List of cuisines available.
        rstn_rating (float): Average customer rating for online ordering.
        rstn_address (str): Physical address of restaurant.
        rstn_chain (bool): Is it a restaurant chain? # Not implemented

    Returns:
        Restaurant (BaseModel): A class object with variables as details
    """

    rstn_id: int
    rstn_name: str
    rstn_city: str
    rstn_locality: str
    rstn_area: str
    rstn_cuisines: List[str]
    rstn_rating: float
    rstn_address: str
    # rstn_chain: bool = False

    @model_validator(mode="before")
    @classmethod
    def extract_and_transform(cls, data):
        main_part = data["cards"][2]["card"]["card"]
        clean_data = {
            "rstn_id": int(main_part["info"].get("id", "-1")),
            "rstn_name": main_part["info"].get("name", ""),
            "rstn_city": main_part["info"].get("city", ""),
            "rstn_locality": main_part["info"].get("locality", ""),
            "rstn_area": main_part["info"].get("areaName", ""),
            "rstn_cuisines": main_part["info"].get("cuisines", ""),
            "rstn_rating": float(main_part["info"].get("avgRating", "-1.0")),
            "rstn_address": main_part["info"]["labels"][1].get("message", ""),
        }
        return clean_data


# Menu has multiple categories called cards
class MenuCards(BaseModel):
    menu_card_list: List[Dict[str, Any]]

    # select a list of cards
    @model_validator(mode="before")
    @classmethod
    def extract_and_transform(cls, data):
        menu_cards = data["cards"][4]["groupedCard"]["cardGroupMap"]["REGULAR"][
            "cards"
        ][1:]
        return {"menu_card_list": menu_cards}

    # filter out the cards thats not needed
    @model_validator(mode="after")
    def filter_valid_cards(self):
        filtered_cards = [
            card
            for card in self.menu_card_list
            if card.get("card", {}).get("card", {}).get("@type", "").split(".")[-1]
            in ["ItemCategory", "NestedItemCategory"]
        ]
        self.menu_card_list = filtered_cards
        return self


# There are multiple items in each menu card category
class MenuItemsList(BaseModel):
    menu_items_list: List[Dict[str, Any]]

    @model_validator(mode="before")
    @classmethod
    def extract_and_transform(cls, data):
        # ItemCategory
        if "itemCards" in list(data["card"]["card"].keys())[2]:
            menu_items = data["card"]["card"]["itemCards"]

        # NestedItemCategory
        elif "categories" in list(data["card"]["card"].keys())[2]:
            categories = data["card"]["card"]["categories"]
            menu_items = [item for catg in categories for item in catg["itemCards"]]

        # Error
        else:
            menu_items = [{}]

        return {"menu_items_list": menu_items}


# The actual food item
class FoodItem(BaseModel):
    food_id: str
    food_name: str
    food_category: str
    food_description: str
    food_price: str
    food_rating: float
    food_type: Literal["VEG", "NONVEG", "EGG", "UNKNOWN"] = "UNKNOWN"  # str#

    @model_validator(mode="before")
    @classmethod
    def extract_and_transform(cls, data):
        main_part = data["card"]["info"]
        clean_data = {
            "food_id": main_part.get("id", ""),
            "food_name": main_part.get("name", ""),
            "food_category": main_part.get("category", ""),
            "food_description": main_part.get("description", ""),
            "food_price": f"Rs.{int(int(main_part.get('price', '-100')) / 100)}",
            "food_rating": float(
                main_part["ratings"]["aggregatedRating"].get("rating", "-1.0")
            ),
            "food_type": main_part["itemAttribute"].get("vegClassifier", "UNKNOWN"),
        }
        return clean_data


# Main class to process menu
class Menu(BaseModel):
    """Pydantic.BaseModel class that returns a list of food items.

    Usage example
    ```python
    >>> menu_data = scraped_json['data']
    >>> menu = Menu(**menu_data)
    >>> menu.food_items
    >>> [
    FoodItem(food_id='146696388', food_name='Pink Pasta Feast Box', food_category='Premium Feast Boxes', food_description='pasta ...', food_price='Rs.450', food_type='VEG', food_rating=3.8),
    FoodItem(food_id='146696386', food_name='Cottage Cheese Steak Box', food_category='Premium Feast Boxes', food_description='cheese steak ...', food_price='Rs.450', food_type='VEG', food_rating=4.4)
    ]
    ```

    Returns:
        Menu (List[FoodItem]): List of `FoodItem` class with food details
    """

    food_items: List[FoodItem]

    @model_validator(mode="before")
    @classmethod
    def extract_and_transform(cls, data):
        menu_cards_list = MenuCards(**data)
        menu_items_list = [
            MenuItemsList(**menu_card) for menu_card in menu_cards_list.menu_card_list
        ]
        food_list = [
            FoodItem(**mi)
            for menu_item in menu_items_list
            for mi in menu_item.menu_items_list
        ]
        return {"food_items": food_list}


class WebShareConfig:
    def __init__(self, instances: int = 6):
        load_dotenv("src/Secrets/Secrets.env")
        domain = os.getenv("DOMAIN")
        port = os.getenv("PORT")
        countries = os.getenv("COUNTRIES").split("-")
        username = f"{os.getenv('PROXY_USERNAME')}{''.join([f'-{x}' for x in countries])}-rotate"
        password = os.getenv("PROXY_PASSWORD")
        server = f"http://{domain}:{port}"

        self.proxy_url = f"http://{username}:{password}@{domain}:{port}"
        self.proxy_configs = [
            ProxyConfig(server=server, username=username, password=password)
            for _ in range(instances)
        ]
        self.proxy_rotation_strat = RoundRobinProxyStrategy(proxies=self.proxy_configs)


class ScrapeConfig:
    def __init__(self, max_parallel: int = 10, len_list: int = 0) -> None:
        self.max_parallel = max_parallel
        self.browser_config = BrowserConfig(
            browser_type="chromium",
            headless=False,  # True, #
            verbose=False,
            enable_stealth=True,
        )

        self.crawler_strat = AsyncPlaywrightCrawlerStrategy(
            browser_config=self.browser_config,
            browser_adapter=UndetectedAdapter(),
        )

        self.run_config_prxy_rot = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            js_code=[
                """await new Promise(r=>setTimeout(r,Math.random()*10000+5000));""",
                """window.location.reload();""",  # Make some randomly chosen javascripts
            ],
            capture_network_requests=True,
            # wait_for="css:html.body.div.div.div:first-child.div.div.div.div:nth-child(2).div:nth-child(2).div.h1",
            proxy_rotation_strategy=WebShareConfig().proxy_rotation_strat,
            stream=False,  # True,  #
        )

        rate_limiter = RateLimiter(
            base_delay=(2, 12),
            max_delay=60.0,
            max_retries=3,
            rate_limit_codes=[429, 503, 403],
        )
        crawl_monitor = CrawlerMonitor(
            urls_total=len_list,
            refresh_rate=0.1,
            enable_ui=False,  # True,  #
            max_width=120,
        )

        self.mem_ada_dispatcher = MemoryAdaptiveDispatcher(
            memory_threshold_percent=80.0,
            max_session_permit=self.max_parallel,
            check_interval=1.0,
            rate_limiter=rate_limiter,
            monitor=crawl_monitor,
        )
