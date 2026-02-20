import os
import re
from typing import Literal

import requests
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
from crawl4ai.async_dispatcher import MemoryAdaptiveDispatcher, RateLimiter
from crawl4ai.browser_adapter import UndetectedAdapter
from crawl4ai.cache_context import CacheMode
from crawl4ai.components.crawler_monitor import CrawlerMonitor
from crawl4ai.proxy_strategy import ProxyConfig, RoundRobinProxyStrategy
from dotenv import load_dotenv


## crawl4ai proxy config
class ProxyDictConfig:
    def __init__(
        self,
        provider: Literal["Scrapeless", "NST", "Massive"] = "Scrapeless",
        instances: int = 4,
        **kwargs,
    ):
        load_dotenv(".env")

        username = password = server = domain = port = pxy_url = ""

        if provider == "Scrapeless":
            kwargs = (
                {"proxyCountry": "IN", "proxyState": "KA", "proxyCity": "bengaluru"}
                if not kwargs
                else kwargs
            )

            proxy_api = os.getenv("PROXY_SCRAPELESS_API_URL", "")
            channel_id = os.getenv("PROXY_SCRAPELESS_CHANNEL_ID")
            api_key = os.getenv("PROXY_SCRAPELESS_API_KEY")

            api_url = proxy_api.format(
                CHANNEL_ID=channel_id,
                proxyCountry=kwargs["proxyCountry"],
                proxyState=kwargs["proxyState"],
                proxyCity=kwargs["proxyCity"],
                API_KEY=api_key,
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

        proxy_configs = [
            ProxyConfig(server=server, username=username, password=password)
            for _ in range(instances)
        ]

        self.proxy_dict = {
            "server": f"http://{domain}:{port}",
            "username": username,
            "password": password,
        }
        self.proxy_url = f"{username}:{password}@{domain}:{port}"
        self.proxy_rotation_strat = RoundRobinProxyStrategy(proxies=proxy_configs)


## crawl4ai scrape config
class ScrapeConfig:
    def __init__(
        self,
        max_parallel: int = 10,
        len_list: int = 0,
        proxy: bool = False,
    ):
        self.browser_config = BrowserConfig(
            browser_type="chromium",
            headless=True,  # False,  #
            verbose=False,
            # enable_stealth=True,
            user_agent_mode="random",
        )

        self.crawler_strat = AsyncPlaywrightCrawlerStrategy(
            browser_config=self.browser_config,
            # browser_adapter=UndetectedAdapter(),
        )

        # rotation_strat = ProxyDictConfig()

        self.run_config_prxy_rot = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            magic=True,
            js_code=[
                """await new Promise(r=>setTimeout(r,Math.random()*6000+5000));""",
            ],
            capture_network_requests=True,
            stream=True,
            # proxy_rotation_strategy=(
            #     rotation_strat.proxy_rotation_strat if proxy else None
            # ),
        )

        rate_limiter = RateLimiter(
            base_delay=(8, 12),
            max_delay=60.0,
            max_retries=3,
            rate_limit_codes=[429, 503, 403],
        )
        # crawl_monitor = CrawlerMonitor(
        #     urls_total=len_list,
        #     refresh_rate=0.1,
        #     enable_ui=False,  # True,  #
        #     max_width=120,
        # )

        self.dispatcher = MemoryAdaptiveDispatcher(
            memory_threshold_percent=90.0,
            max_session_permit=max_parallel,
            check_interval=1.0,
            rate_limiter=rate_limiter,
            # monitor=crawl_monitor,
        )
