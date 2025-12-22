import os
from dotenv import load_dotenv
from crawl4ai.cache_context import CacheMode
from crawl4ai.components.crawler_monitor import CrawlerMonitor
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.proxy_strategy import RoundRobinProxyStrategy, ProxyConfig
from crawl4ai.async_dispatcher import RateLimiter, MemoryAdaptiveDispatcher


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
        self.browser_config = BrowserConfig(
            browser_type="chromium",
            headless=True,  # False,  #
            verbose=False,
            enable_stealth=True,
        )

        self.run_config_prxy_rot = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            js_code=[
                """await new Promise(r=>setTimeout(r,Math.random()*10000+1000));"""
            ],
            proxy_rotation_strategy=WebShareConfig().proxy_rotation_strat,
        )

        self.run_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            js_code=[
                """await new Promise(r=>setTimeout(r,Math.random()*10000+1000));"""
            ],
        )

        rate_limiter = RateLimiter(
            base_delay=(2, 3),
            max_delay=60.0,
            max_retries=3,
            rate_limit_codes=[429, 503, 403],
        )
        crawl_monitor = CrawlerMonitor(
            urls_total=len_list,
            refresh_rate=0.1,
            enable_ui=True,
            max_width=120,
        )

        self.mem_ada_dispatcher = MemoryAdaptiveDispatcher(
            memory_threshold_percent=80.0,
            max_session_permit=max_parallel,
            check_interval=1.0,
            rate_limiter=rate_limiter,
            monitor=crawl_monitor,
        )
