import json
import pandas as pd
from random import choice
from urllib.parse import quote
from typing import Dict, Any, List
from crawl4ai.async_webcrawler import AsyncWebCrawler

from src.ETL.ETL_Config import ScrapeConfig
from src.ETL.ETL_Constants import SwiggyRestaurantConstants
from src.Utils.main_utils import save_json, save_dataframe
from src.Logging.logger import log_etl
from src.Exception.exception import LogException, CustomException


class RestaurantData:
    def __init__(
        self,
        use_proxy_rotation: bool = False,
        crawl_config: ScrapeConfig = ScrapeConfig(),
    ) -> None:
        try:
            self.use_proxy_rotation = use_proxy_rotation
            self.crawl_config = crawl_config

        except Exception as e:
            LogException(e, logger=log_etl)
            raise CustomException(e)

    async def get(self) -> pd.DataFrame:
        clean_data = pd.DataFrame({"data": ["Error in RestaurantData().get()"]})
        try:
            log_etl.info("Extraction: Preparing to scrape restaurant data")
            json_data = await self._get_json_data()

            log_etl.info("Extraction: Preparing to clean scraped restaurant data")
            clean_data = self._get_clean_data(json_data)

        except Exception as e:
            LogException(e, logger=log_etl)
            raise CustomException(e)

        return clean_data

    async def _get_json_data(self) -> List[Dict[str, Any]]:
        json_data = [{"data": "Error in RestaurantData()._get_json_data()"}]
        save_path_json = SwiggyRestaurantConstants.JSON_FILE_SAVE_PATH
        try:
            log_etl.info("Extraction: Preparing list of URLs to scrape")
            urls_list = RestaurantData.get_urls_list()

            log_etl.info("Extraction: Starting data scraping")
            async with AsyncWebCrawler(
                config=self.crawl_config.browser_config
            ) as crawler:
                try:
                    results = await crawler.arun_many(
                        urls=urls_list,
                        dispatcher=self.crawl_config.mem_ada_dispatcher,
                        config=self.crawl_config.run_config_prxy_rot
                        if self.use_proxy_rotation
                        else self.crawl_config.run_config,
                    )

                    log_etl.info("Extraction: Formatting scraped data")
                    json_data = []
                    for result in results:
                        json_data_str = json.loads(result.extracted_content)
                        json_data.append(
                            json.loads(json_data_str[0]["swiggy_json_data"])
                        )

                except Exception as e:
                    LogException(e, logger=log_etl)

        except Exception as e:
            LogException(e, logger=log_etl)
            raise CustomException(e)

        save_json(data=json_data, save_path=save_path_json)
        return json_data

    def _get_clean_data(self, data_list) -> pd.DataFrame:
        clean_data = pd.DataFrame()
        save_path_df = SwiggyRestaurantConstants.DF_FILE_SAVE_PATH
        try:
            for data in data_list:
                if data["data"]["statusMessage"] in ["done successfully"]:
                    restaurant_list: list[dict] = data["data"]["cards"][1][
                        "groupedCard"
                    ]["cardGroupMap"]["RESTAURANT"]["cards"]

                    restaurant_data = []
                    for card in restaurant_list:
                        info = card["card"]["card"]["info"]
                        try:
                            restaurant_data.append(
                                {
                                    "restaurant_id": int(info.get("id", "-1")),
                                    "restaurant_name": info["name"],
                                    "city": info["slugs"]["city"],
                                    "address": info["address"],
                                    "locality": info["locality"],
                                    "area": info["areaName"],
                                    "cuisines": ", ".join(
                                        [item for item in info["cuisines"]]
                                    ),
                                    "average_rating": float(
                                        info.get("avgRating", "-1.0")
                                    ),
                                }
                            )
                        except Exception as e:
                            print(f"Restaurant {info['name']}. Error: {e}")
                            continue

                    clean_data = pd.concat(
                        [clean_data, pd.DataFrame(restaurant_data)],
                        axis=0,
                        ignore_index=True,
                    )

                else:
                    log_etl.info("Extraction: JSON statusMessage != 'Success'")
                    continue

        except Exception as e:
            LogException(e, logger=log_etl)
            raise CustomException(e)

        save_dataframe(data=clean_data, save_path=save_path_df)
        return clean_data

    @staticmethod
    def get_urls_list() -> List[str]:
        """Method to get a list of API endpoint URLs of Swiggy.

        Raises:
            CustomException: Any error during the function.

        Returns:
            urls_list (List[str]): List of API endpoint URLs.
        """
        urls_list = [""]
        try:
            # get variables
            api_endpoint = SwiggyRestaurantConstants.SWIGGY_API_ENDPOINT
            coords_json = SwiggyRestaurantConstants.COORDINATES_JSON
            queries = SwiggyRestaurantConstants.QUERIES

            # flatten the data to get list[tuples] of coordinates
            coords_list = [
                tuple(area["area_coords"])
                for country in coords_json["Countries"]
                for state in country["States"]
                for city in state["Cities"]
                for area in city["Areas"]
            ]

            # format api endpoint with coordinates and random query
            urls_list = [
                api_endpoint.format(
                    latitude=coords[0],
                    longitude=coords[1],
                    query=quote(choice(queries)),
                )
                for coords in coords_list
            ]
            log_etl.info("Extraction: Successfully prepared URLs list")

        except Exception as e:
            LogException(e, logger=log_etl)
            raise CustomException(e)

        return urls_list
