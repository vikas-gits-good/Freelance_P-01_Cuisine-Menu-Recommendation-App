import os
import re
import requests
from dotenv import load_dotenv
from typing import Literal

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

from src.Exception.exception import LogException, CustomException


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
