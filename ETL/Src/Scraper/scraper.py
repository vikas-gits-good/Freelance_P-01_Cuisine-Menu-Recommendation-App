import asyncio
import json
import re
from typing import Any, AsyncGenerator, Dict, List, Literal, Tuple

from crawl4ai.async_webcrawler import AsyncWebCrawler
from dotenv import load_dotenv

from Src.Config import Menu, MongoDBConfig, Restaurant, ScrapeConfig
from Src.Constants.database import MDBIndexKey
from Src.Utils import (
    LogException,
    get_cities_from_redis,
    get_urls_from_redis,
    log_etl,
    put_urls_to_redis,
    upsert_to_mongodb,
)


class RestaurantDataScraper:
    """Class that scrapes restaurant data in parallel and upserts data to MongoDB"""

    def __init__(
        self,
        batch_size: int = 100,
        sc_config: ScrapeConfig = ScrapeConfig(),
        mc_config: MongoDBConfig = MongoDBConfig(),
    ):
        load_dotenv(".env")
        self.batch_size = batch_size
        self.sc_config = sc_config
        self.mc_config = mc_config

    def get(self):
        """Main entry api. Call this after init to start scraping"""
        try:
            asyncio.run(self._scrape_all_cities())

        except Exception as e:
            LogException(e, logger=log_etl)
            # raise CustomException(e)

    async def _scrape_all_cities(self):
        log_etl.info("Extraction: Getting urls to crawl")
        # get city names from redis keys itself. city will have '-'
        city_list = [item.split(":")[-1] for item in get_cities_from_redis()]

        for city in city_list:
            batch_json_data: List[Dict[str, Any]] = []
            count = 0
            while True:
                urls_list = get_urls_from_redis(
                    key=f"urls:{city}",
                    batch_size=self.batch_size,
                )
                if len(urls_list) == 0:
                    log_etl.info(f"Extraction: 'urls:{city}' is empty. Moving on")
                    break

                log_etl.info(
                    f"Extraction: Scraping menu data from {len(urls_list)} restaurants in '{city}'"
                )
                # Process streaming data as it arrives
                async for menu_data, json_data in self._scrape_one_city(
                    urls_list, city
                ):
                    try:
                        batch_json_data.append(
                            {
                                "rstn_id": menu_data.ids,
                                "rstn_city": menu_data.city_id,
                                "rstn_data": json_data,
                            }
                        )

                        count += 1
                        if len(batch_json_data) == self.batch_size:
                            log_etl.info(
                                f"Extraction: Saving a batch of {count} restaurants"
                            )
                            upsert_to_mongodb(
                                data=batch_json_data,
                                database=self.mc_config.swiggy.database,
                                collection=self.mc_config.swiggy.coll_scrp_data,
                                idx_key=MDBIndexKey.RESTAURANT_ID,
                            )
                            batch_json_data = []

                    except Exception as e:
                        LogException(e, logger=log_etl)
                        continue

            # Save final batch of city
            log_etl.info(
                f"Extraction: Saving final batch of {len(batch_json_data)} restaurants. Total count: {count}"
            )
            upsert_to_mongodb(
                data=batch_json_data,
                database=self.mc_config.swiggy.database,
                collection=self.mc_config.swiggy.coll_scrp_data,
                idx_key=MDBIndexKey.RESTAURANT_ID,
            )

            log_etl.info("Extraction: Upserting failed urls to MongoDB")
            urls_list_1 = get_urls_from_redis(
                key=f"urls:{city}",
                purpose="update",
                database="1",
            )
            urls_list_2 = get_urls_from_redis(
                key=f"urls:{city}",
                purpose="update",
                database="2",
            )
            failed_data = self._modify_failed_urls(urls_list_1, urls_list_2)
            upsert_to_mongodb(
                data=failed_data,
                database=self.mc_config.swiggy.database,
                collection=self.mc_config.swiggy.coll_upst_fail,
                idx_key=MDBIndexKey.RESTAURANT_ID,
            )

    async def _scrape_one_city(
        self,
        urls: List[str],
        city: str,
    ) -> AsyncGenerator[Tuple[Restaurant, Dict[str, Any]]]:
        try:
            async with AsyncWebCrawler(
                crawler_strategy=self.sc_config.crawler_strat,
                config=self.sc_config.browser_config,
            ) as crawler:
                results = await crawler.arun_many(
                    urls=urls,
                    config=self.sc_config.run_config_prxy_rot,
                    dispatcher=self.sc_config.dispatcher,
                )
                async for result in results:
                    try:
                        for r in result.network_requests:
                            # parse string and extract json
                            if r[
                                "event_type"
                            ] == "response" and "/dapi/menu/pl?" in r.get("url", ""):
                                json_data: dict = json.loads(r["body"]["text"])
                                menu_data = self._extract_menu(json_data)
                                yield menu_data[0], json_data

                    except Exception as e:
                        LogException(e, logger=log_etl)
                        data = {
                            "city": city,
                            "url": result.url,
                            "status_code": result.status_code,
                            "error_message": str(e),
                        }
                        log_etl.info(f"Error: {data}")
                        if str(e) == "'cards'":
                            put_urls_to_redis(  # restaurants are shut down
                                key=f"urls:{city}",
                                data_list=[result.url],
                                database="2",
                            )
                        elif str(e) == "list index out of range":
                            put_urls_to_redis(  # restaurant has no menu
                                key=f"urls:{city}",
                                data_list=[result.url],
                                database="1",
                            )
                        else:  # this could make it an infinite while loop
                            put_urls_to_redis(  # reload back to queue
                                key=f"urls:{city}",
                                data_list=[result.url],
                                database="0",
                            )
                        continue

        except Exception as e:
            LogException(e, logger=log_etl)
            # raise CustomException(e)

    @staticmethod
    def _extract_menu(json_data: dict) -> Tuple[Restaurant, Menu]:
        # keep Menu also as some restaurants have rstn data but not menu data
        return (Restaurant(**json_data["data"]), Menu(**json_data["data"]))

    @staticmethod
    def _modify_failed_urls(
        list1: List[str],
        list2: List[str],
    ) -> List[Dict[str, Any]]:
        def _process(
            data: list, source: Literal["1", "2"] = "1"
        ) -> List[Dict[str, Any]]:
            _data = []
            for url in data:
                try:
                    match = re.search(r"/city/([^/]+)/.*-rest(\d+)", url)
                    city = re.sub(r"[,-_]", " ", match.group(1)).strip()
                    rstn_id = int(match.group(2).strip())
                    _data.append(
                        {
                            "rstn_id": rstn_id,
                            "rstn_city": city,
                            "rstn_data": {
                                "ids": rstn_id,
                                "url": url,
                                "city": city,
                                "reason": "No Menu"
                                if source == "1"
                                else "No Restaurant",
                            },
                        }
                    )

                except Exception as e:
                    LogException(e, logger=log_etl)
                    log_etl.info(f"Error: '{url}' didnt match regex pattern")
                    continue

            return _data

        return _process(list1, source="1") + _process(list2, source="2")
