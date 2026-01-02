import re
import os
import random
import asyncio as asc
from datetime import datetime
from typing import List, AsyncGenerator
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from camoufox.async_api import AsyncCamoufox
from camoufox.utils import launch_options

from src.Utils.main_utils import get_from_mongodb, save_json, upsert_to_mongodb
from src.Config import MongoDBConfig
from src.ETL.ETL_Config import BrowserSessionConfig, ProxyDictConfig

from src.Logging.logger import log_etl
from src.Exception.exception import LogException, CustomException


class GenerateBrowsers:
    def __init__(
        self,
        md_config: MongoDBConfig = MongoDBConfig(),
        bw_config: BrowserSessionConfig = BrowserSessionConfig(),
    ):
        self.md_config = md_config
        self.bw_config = bw_config
        self.results_queue = asc.Queue()

    async def start(self):
        # get 'city_rstn_coords_data.json' from mongodb
        # prepare a list of data to scrape.
        # choose 20 cities and 20 links from each city with proxy
        log_etl.info("Extraction: Preparing data to scrape")
        city_dict = self._get_city_data(limit=20)

        # create folders for each city
        log_etl.info("Extraction: Creating folders to store browser data")
        for city in city_dict.keys():
            path = self.bw_config.browser_path.format(session_id=city)
            os.makedirs(path, exist_ok=True)

        # use parallel processing to choose to scrape 4 cities at a time
        # prepare the data saving config
        total_urls = sum(len(city_dict[city]["rstn_urls"]) for city in city_dict)
        saver_task = asc.create_task(self._batch_saver(total_urls))

        # each city scraper will init a new browser instance.
        # if this instance succeeds, save this browser info, fingerprint & session id
        # src/ETL/ETL_Data/browser/{city}/{session_id}/fingerprint/ -> store fingerprint.json
        # src/ETL/ETL_Data/browser/{city}/{session_id}/ -> store camoufox data
        city_tasks = [
            asc.create_task(
                self.process_city_stream(
                    city, city_dict[city]["rstn_url"], city_dict[city]["proxy"]
                )
            )
            for city in city_dict.keys()
        ]

        # Wait for all city tasks to complete
        await asc.gather(*city_tasks)

        # Wait for batch saver to finish
        await saver_task

        # repeat above step till you have created enough unique browser-session id that
        # is 10% length of urls for each city.
        # some cities have < 10 urls. 1 browser is enough in such cases.

    def _get_city_data(self, limit: int | None = None):
        try:
            city_dict = get_from_mongodb(
                database=self.md_config.swiggy.database,
                collection=self.md_config.swiggy.coll_rstn_cnfg,
                prefix="Extraction",
            )

            city_data = {}

            for city in list(city_dict.keys())[:limit]:
                urls = [rstn["rstn_url"] for rstn in city_dict[city]["restaurants"]]
                city_data.update(
                    {
                        city: {
                            "rstn_url": urls[:limit],
                            "proxy": city_dict[city]["proxy"],
                        }
                    }
                )

            return city_data

        except Exception as e:
            LogException(e, logger=log_etl)
            raise CustomException(e)

    async def _batch_saver(self, total_urls: int):
        """Collect streamed JSON results from queue and save in batches"""
        try:
            batch = []
            batch_num = 0
            processed = 0

            while processed < total_urls:
                result = await self.results_queue.get()
                batch.append(result)
                processed += 1

                # Save batch when full or all results processed
                if len(batch) >= self.bw_config.batch_size or processed == total_urls:
                    file_path = self.bw_config.save_data_path.format(batch=batch_num)
                    save_json(batch, file_path)
                    upsert_to_mongodb(
                        data=batch,
                        database=self.md_config.swiggy.database,
                        collection=self.md_config.swiggy.coll_scrp_data,
                        prefix="Extraction",
                    )
                    log_etl.info(
                        f"Extraction: Saved batch-{batch_num:,04d} with {len(batch)} results to '{file_path}' & MongoDB"
                    )
                    batch = []
                    batch_num += 1

            log_etl.info(f"Extraction: All results saved in {batch_num:,04d} batches")

        except Exception as e:
            LogException(e, logger=log_etl)
            raise CustomException(e)

    async def process_city_stream(self, city, urls, proxy):
        """Process a city and add results to queue for streaming"""
        async for result in self.crawl_city(city, urls, proxy):
            await self.results_queue.put(result)

    async def crawl_city(
        self,
        city: str,
        urls: List[str],
        proxy: str,
    ) -> AsyncGenerator[dict, None]:
        """Crawl all restaurants for a single city in its own browser instance"""
        log_etl.info(
            f"Extraction: Starting browser instance for {len(urls)} restaurants in '{city}' city"
        )
        # setup city wise launch_options
        kwargs = {
            key: value
            for key, value in zip(
                ["proxyCountry", "proxyState", "proxyCity"], proxy.split("-")
            )
        }
        pdc = ProxyDictConfig(provider="Scrapeless", kwargs=kwargs)
        pxy = pdc.pxy
        config_data = launch_options(
            geoip=True,
            block_webrtc=True,
            humanize=True,
            proxy=pxy,
        )
        time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        bw_save_path = self.bw_config.save_data_path.format(session_id=f"{city}/{time}")
        # I need a new browser instance for every 10 urls processed
        async with AsyncCamoufox(
            from_options=config_data,
            persistent_context=True,
            user_data_dir=bw_save_path,
        ) as browser:
            semaphore = asc.Semaphore(self.bw_config.max_scrp_per_city)

            async def fetch_with_semaphore(url: str):
                async with semaphore:
                    initial_delay = random.uniform(0.5, 2.0)
                    await asc.sleep(initial_delay)

                    page = await browser.new_page()
                    try:
                        result = await self.fetch_restaurant(url, city, page)
                        return result

                    finally:
                        initial_delay = random.uniform(0.5, 2.0)
                        await asc.sleep(initial_delay)
                        await page.close()

            # Create tasks for all URLs
            tasks = [fetch_with_semaphore(url) for url in urls]

            # Process results as they complete (streaming)
            for coro in asc.as_completed(tasks):
                try:
                    result = await coro
                    yield result

                except Exception as e:
                    log_etl.error(f"Extraction: [{city}] Failed after 3 retries: {e}")
                    yield {}

        log_etl.info(
            f"Extraction: [{city}] Browser instance closed. Saving fingerprint"
        )
        fp_save_path = self.bw_config.fingerprint_path.format(
            session_id=f"{city}/{time}"
        )
        save_json(config_data, fp_save_path)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((TimeoutError, Exception)),
        reraise=True,
    )
    async def fetch_restaurant(self, url: str, city: str, page):
        """Fetch a single restaurant URL with retry logic"""
        try:
            # Random delay for rate limiting
            delay = random.uniform(*self.bw_config.rate_limit_range)
            await asc.sleep(delay)

            log_etl.info(f"Extraction: [{city}] Fetching: {url}")

            async with page.expect_response(
                re.compile(r"/dapi/menu/pl")
            ) as response_info:
                await page.goto(url, timeout=15000)

            response = await response_info.value

            if response.status == 200:
                json_data = await response.json()
                return json_data

            else:
                log_etl.warning(f"[{city}] Non-200 status ({response.status}): {url}")

        except Exception as e:
            log_etl.info(f"Error processing [{city}], [{url}]")
            LogException(e, logger=log_etl)
