import os
import re
import requests
from dataclasses import dataclass
from dotenv import load_dotenv
from typing import Literal, List, Dict, Any
from pydantic import BaseModel, model_validator

from crawl4ai.cache_context import CacheMode
from crawl4ai.components.crawler_monitor import CrawlerMonitor
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.proxy_strategy import RoundRobinProxyStrategy, ProxyConfig
from crawl4ai.async_dispatcher import RateLimiter, MemoryAdaptiveDispatcher
from crawl4ai.browser_adapter import UndetectedAdapter
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
from src.ETL.Constants import (
    SwiggyLinksConstants,
    NominatimOSMConstants,
    RestaurantConstants,
    ProxyConstants,
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
        self.read_proxy_data_path = os.path.join(
            ProxyConstants.PROXY_CITY_JSON_DIRECTORY,
            ProxyConstants.PROXY_CITY_JSON_FILE_NAME,
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
            NominatimOSMConstants.UNIQUE_DATA_SAVE_DIRECTORY,
            NominatimOSMConstants.UNIQUE_DATA_FILE_NAME,
        )
        self.save_json_data_path = os.path.join(
            RestaurantConstants.UNIQUE_DATA_SAVE_DIRECTORY,
            RestaurantConstants.UNIQUE_DATA_FILE_NAME,
        )
        self.save_unique_data_path = os.path.join(
            RestaurantConstants.UNIQUE_DATA_SAVE_DIRECTORY,
            RestaurantConstants.UNIQUE_DATA_FILE_NAME,
        )
        self.menu_api_ep = RestaurantConstants.RESTAURANT_MENU_ENDPOINT


# Restaurant details to scrape from json
class Restaurant(BaseModel):
    """pydantic.BaseModel that returns restaurant details from scraped JSON.

    ## Usage:
    ```python
    >>> rstn = Restaurant(**json_data['data'])
    >>> rstn
    >>> Restaurant(ids=8840, name='Smoke House Deli', city='Delhi', locality='Saket', area='Saket', cuisines=['Pizzas', 'Pastas'], rating=4.2, address='...', coords='28.5286078,77.2160345', chain=True)
    ```
    Attributes:
        ids (int): Unique ID for each restaurants. Default -1.
        name (str): Restaurant name. Default ''.
        city (str): City of restaurant. Default ''.
        area (str): Area of restaurant. Default ''.
        locality (str): Locality of restaurant. Default ''.
        cuisines (List['str']): List of cuisines available. Default [''].
        rating (float): Average customer rating for online ordering. Default -1.0.
        address (str): Physical address of restaurant. Default ''.
        coords (str): Latitude, Longitude coordinates of restaurant. Default ''.
        chain (bool): Is this a restaurant chain? Default False.

    Returns:
        Restaurant (BaseModel): A class object with variables as details
    """

    ids: int = -1
    name: str = ""
    city: str = ""
    area: str = ""
    locality: str = ""
    cuisines: List[str] = [""]
    rating: float = -1.0
    address: str = ""
    coords: str = ""
    chain: bool = False

    @model_validator(mode="before")
    @classmethod
    def extract_and_transform(cls, data):
        main_part = data["cards"][2]["card"]["card"]
        clean_data = {
            "ids": int(main_part["info"].get("id", "-1")),
            "name": main_part["info"].get("name", ""),
            "city": main_part["info"].get("city", ""),
            "area": main_part["info"].get("areaName", ""),
            "locality": main_part["info"].get("locality", ""),
            "cuisines": main_part["info"].get("cuisines", [""]),
            "rating": float(main_part["info"].get("avgRating", "-1.0")),
            "address": main_part["info"]["labels"][1].get("message", ""),
            "coords": main_part["info"].get("latLong", ""),
            "chain": main_part["info"].get("multiOutlet", False),
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
    # ids: str = "" # leave this out.
    name: str = ""
    category: str = ""
    description: str = ""
    price: int = -1
    rating: float = -1.0
    types: Literal["VEG", "NONVEG", "EGG", "UNKNOWN"] = "UNKNOWN"
    cuisine: str = ""  # make subcuisine later, maincuisine now

    @model_validator(mode="before")
    @classmethod
    def extract_and_transform(cls, data):
        main_part = data["card"]["info"]
        clean_data = {
            # "ids": main_part.get("id", ""),
            "name": main_part.get("name", ""),
            "category": main_part.get("category", ""),
            "description": main_part.get("description", ""),
            "price": round(int(main_part.get("price", "-100")) / 100),
            "rating": float(
                main_part["ratings"]["aggregatedRating"].get("rating", "-1.0")
            ),
            "types": main_part["itemAttribute"].get("vegClassifier", "UNKNOWN"),
        }
        return clean_data


# Main class to process menu
class Menu(BaseModel):
    """Pydantic.BaseModel class that returns a list of food items.

    ## Usage:
    ```python
    >>> menu = Menu(**json_data['data'])
    >>> menu.food_items
    >>> [
    FoodItem(ids='146696388', name='Pink Pasta Feast Box', category='Premium Feast Boxes', description='pasta ...', price='Rs.450', types='VEG', rating=3.8),
    FoodItem(ids='146696386', name='Cottage Cheese Steak Box', category='Premium Feast Boxes', description='cheese steak ...', price='Rs.450', types='VEG', rating=4.4)
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

        @dataclass
        class Creds:
            domain = os.getenv("DOMAIN")
            port = os.getenv("PORT")
            countries = os.getenv("COUNTRIES").split("-")
            username = f"{os.getenv('PROXY_USERNAME')}{''.join([f'-{x}' for x in countries])}-rotate"
            password = os.getenv("PROXY_PASSWORD")
            server = f"http://{domain}:{port}"

        proxy_configs = [
            ProxyConfig(
                server=Creds.server, username=Creds.username, password=Creds.password
            )
            for _ in range(instances)
        ]
        self.creds = Creds
        self.proxy_url = (
            f"http://{Creds.username}:{Creds.password}@{Creds.domain}:{Creds.port}"
        )
        self.proxy_rotation_strat = RoundRobinProxyStrategy(proxies=proxy_configs)


class ProxyDictConfig:
    def __init__(
        self,
        provider: Literal["Scrapeless", "NST", "Massive"] = "Scrapeless",
        instances: int = 4,
        **kwargs,
    ):
        load_dotenv("src/Secrets/proxy.env")
        PROXY_DICT = os.getenv("PROXY_DICT", {})[provider]

        if provider == "Scrapeless":
            kwargs = (
                {"proxyCountry": "IN", "proxyState": "KA", "proxyCity": "bengaluru"}
                if not kwargs
                else kwargs
            )
            api_url = PROXY_DICT["API_URL"].format(
                CHANNEL_ID=PROXY_DICT["CHANNEL_ID"],
                proxyCountry=kwargs["proxyCountry"],
                proxyState=kwargs["proxyState"],
                proxyCity=kwargs["proxyCity"],
                API_KEY=PROXY_DICT["API_KEY"],
            )
            resp = requests.get(api_url)
            if resp.status_code == 200:
                pxy_url = resp.text
            match = re.search(r"([^:]+):([^@]+)@([^:]+):(\d+)", pxy_url).groups()
            username = match[0]
            password = match[1]
            domain = re.sub(r"gw-[a-z]+", "gw-ap", match[2])
            port = match[3]
            server = f"http://{domain}:{port}"

        elif provider == "NST":
            username = f""
            password = f""
            domain = f""
            port = f""
            server = f"http://{domain}:{port}"

        elif provider == "Massive":
            username = f""
            password = f""
            domain = f""
            port = f""
            server = f"http://{domain}:{port}"

        proxy_configs = [
            ProxyConfig(server=server, username=username, password=password)
            for _ in range(instances)
        ]

        self.pxy = {
            "server": f"http://{domain}:{port}",
            "username": username,
            "password": password,
        }
        self.proxy_url = f"{username}:{password}@{domain}:{port}"
        self.proxy_rotation_strat = RoundRobinProxyStrategy(proxies=proxy_configs)


class ScrapeConfig:
    def __init__(self, max_parallel: int = 10, len_list: int = 0) -> None:
        self.max_parallel = max_parallel
        self.browser_config = BrowserConfig(
            browser_type="chromium",
            headless=False,  # True, #
            verbose=False,
            enable_stealth=True,
            user_agent_mode="random",
        )

        self.crawler_strat = AsyncPlaywrightCrawlerStrategy(
            browser_config=self.browser_config,
            browser_adapter=UndetectedAdapter(),
        )

        self.run_config_prxy_rot = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            magic=True,
            js_code=[
                """await new Promise(r=>setTimeout(r,Math.random()*5000+5000));""",
            ],
            capture_network_requests=True,
            stream=True,
        )

        rate_limiter = RateLimiter(
            base_delay=(8, 12),
            max_delay=30.0,
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
            memory_threshold_percent=90.0,
            max_session_permit=self.max_parallel,
            check_interval=1.0,
            rate_limiter=rate_limiter,
            monitor=crawl_monitor,
        )
