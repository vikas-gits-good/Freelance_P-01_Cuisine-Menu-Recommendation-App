import re
import gzip
import json
import requests
import pandas as pd
from random import choice
from requests import Response
from urllib.parse import quote
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Literal
from crawl4ai.async_webcrawler import AsyncWebCrawler

from lxml import etree
from pathlib import Path
import time

from src.ETL.ETL_Config import ScrapeConfig, LinksConfig, CoordsConfig
from src.ETL.ETL_Constants import SwiggyRestaurantConstants
from src.Utils.main_utils import save_json, save_dataframe, read_json
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


class AllLinks:
    def __init__(self, config: LinksConfig = LinksConfig()) -> None:
        self.config = config

    def get(self):
        try:
            log_etl.info("Extraction: Getting main sitemap file")
            main_xml: Response = self._get(url=self.config.main_link)
            log_etl.info(
                f"Extraction: Sitemap: {main_xml.url} | Status: {main_xml.status_code}"
            )

            if main_xml.status_code == 200:
                main_path = self.config.get_path(self.config.main_link)
                self._save(main_xml, main_path)

            log_etl.info("Extraction: Getting sub-sitemap files")
            child_sitemaps = self._read_sitemap_index(main_path)
            child_xmls: list[Response] = [
                self._get(url=link) for link in child_sitemaps
            ]
            child_paths = [self.config.get_path(child.url) for child in child_xmls]

            _ = [
                log_etl.info(
                    f"Extraction: Sitemap: {child.url} | Status: {child.status_code}"
                )
                for child in child_xmls
            ]

            for child, path in zip(child_xmls, child_paths):
                if child.status_code == 200:
                    self._save(child, path)
                else:
                    print(f"Error with {child.url.split('/')[-1]}. Skipping")
                    continue

            log_etl.info(
                "Extraction: Getting full sitemap of Swiggy! This is a slow process > 20 minutes."
            )
            _ = self._extract_urls(path_list=child_paths)

            log_etl.info("Extraction: Getting city and restaurants details from urls")
            _ = self.get_data_from_url()

        except Exception as e:
            LogException(e, logger=log_etl)
            raise CustomException(e)

    def _get(self, url):
        return requests.get(url, headers=self.config.headers, timeout=10)

    def _save(self, obj, path):
        with open(path, "wb") as f:
            f.write(obj.content)

    def _read_sitemap_index(self, path):
        with gzip.open(path, "rb") as f:
            content = f.read()

        root = ET.fromstring(content)
        namespaces = {"sitemap": "http://www.sitemaps.org/schemas/sitemap/0.9"}

        child_sitemaps = []
        for sitemap in root.findall(".//sitemap:sitemap", namespaces):
            loc = sitemap.find("sitemap:loc", namespaces).text
            child_sitemaps.append(loc)

        return child_sitemaps

    def _extract_urls(self, path_list, batch_size=50000):
        """Process 65 local .xml.gz sitemaps, extract URLs, save as JSON"""
        all_urls = []
        output_file = self.config.all_urls_file_path
        temp_file = Path(output_file).with_suffix(".tmp")

        for i, sitemap_file in enumerate(path_list, 1):
            urls_in_file = 0
            context = etree.iterparse(
                gzip.open(sitemap_file, "rb"),
                events=("end",),
                tag="{http://www.sitemaps.org/schemas/sitemap/0.9}url",
            )

            for event, elem in context:
                # Extract URL
                loc = elem.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
                if loc is not None and loc.text:
                    all_urls.append(loc.text)
                    urls_in_file += 1

                    # Batch save every 50K URLs
                    if len(all_urls) >= batch_size:
                        self._save_batch(all_urls, temp_file)
                        all_urls = []
                        log_etl.info(
                            f"Extraction: Saved Batch-{i:02d} of extracted urls"
                        )

                # Clear memory
                elem.clear()
                while elem.getprevious() is not None:
                    del elem.getparent()[0]

            time.sleep(0.1)  # Brief pause

        # Final batch
        if all_urls:
            self._save_batch(all_urls, temp_file)
            log_etl.info("Extraction: Saved final batch of extracted urls")

        # Rename to final file
        temp_file.rename(output_file)

    def _save_batch(self, urls, filepath):
        """Append batch to JSON file"""
        try:
            with open(filepath, "r+") as f:
                data = json.load(f)
                data["links"].extend(urls)
                f.seek(0)
                f.truncate()
                json.dump(data, f, separators=(",", ":"))

        except FileNotFoundError:
            with open(filepath, "w") as f:
                json.dump({"links": urls}, f, separators=(",", ":"))

    def get_data_from_url(self):
        try:
            read_path = self.config.all_urls_file_path
            save_path = self.config.unique_data_file_path

            urls_dict = read_json(save_path=read_path)
            urls_list = urls_dict["links"]
            search_pattern = r"https://www\.swiggy\.com/city/([^/]+)/(.+)-rest(\d+)"

            log_etl.info("Extraction: Reading 3M+ urls and extracting data")
            main_data = {}

            def clean_string(text):
                keywords = [
                    "-only-dominos",
                    "-dominos-only",
                    "-and-",
                    "-road",
                    "-do-not-use",
                    "-new-city",
                    "closed",
                    "-please-use-city-noida-city-id-24",
                ]
                if any(keyword in text for keyword in keywords):
                    return text.split("-")[0]
                text = text.replace("jjajjar", "jhajjar")
                return text.replace("-", " ")

            for url in urls_list:
                match = re.search(search_pattern, url)
                if match:
                    city = match.group(1)
                    city = clean_string(city)
                    rstn_id = int(match.group(3))

                    # Create a new dict for each new city
                    if city not in main_data.keys():
                        main_data.update(
                            {
                                city: {
                                    "name": "",
                                    "coords": [],
                                    "boundingbox": [],
                                    "address": {},
                                    "restaurants": [],
                                }
                            }
                        )

                    # Append data to ['city']['restaurants']
                    main_data[city]["restaurants"].append(
                        {"rstn_id": rstn_id, "rstn_url": url}
                    )

            log_etl.info("Extraction: Rearranging extracted data")
            main_data = dict(sorted(main_data.items()))

            log_etl.info("Extraction: Saving extracted data")
            save_json(data=main_data, save_path=save_path)

        except Exception as e:
            LogException(e, logger=log_etl)
            raise CustomException(e)


class CityCoordinates:
    def __init__(
        self,
        source: Literal["OSM", "GMaps"] = "OSM",
        config: CoordsConfig = CoordsConfig(),
    ) -> None:
        self.config = config
        self.source = source  # some address details is missing in OSM

    def get(self):
        try:
            read_path = self.config.read_unique_data_path
            save_path = self.config.save_unique_data_path
            rqst_parm = self.config.request_params

            city_dict = read_json(save_path=read_path)

            log_etl.info(
                f"Extraction: Getting {len(list(city_dict.keys())):04d} cities' coordinates & address details. This will take > 10 minutes."
            )
            cnt = 1

            for city in city_dict.keys():
                try:
                    # prep request parameters
                    rp = {
                        "url": rqst_parm["url"].format(query=quote(f"{city} in India")),
                        "headers": rqst_parm["headers"],
                        "timeout": rqst_parm["timeout"],
                    }

                    # make api call

                    response = requests.get(**rp)
                    if response.status_code == 200:
                        json_data = response.json()

                        if json_data:
                            city_dict[city].update(
                                {"name": json_data[0]["display_name"]}
                            )
                            city_dict[city].update(
                                {
                                    "coords": [
                                        float(json_data[0]["lat"]),
                                        float(json_data[0]["lon"]),
                                    ]
                                }
                            )
                            if "address" in json_data[0].keys():
                                city_dict[city].update(
                                    {"address": json_data[0]["address"]}
                                )
                            city_dict[city].update(
                                {
                                    "boundingbox": [
                                        float(data)
                                        for data in json_data[0]["boundingbox"]
                                    ]
                                }
                            )

                        else:
                            log_etl.info(
                                f"Extraction: Coordinates not found for '{city}'. Continuing"
                            )

                    if cnt % 100 == 0:
                        log_etl.info(
                            f"Extraction: Completed {cnt:04d} of {len(list(city_dict.keys())):04d} urls."
                        )
                        time.sleep(10)

                    cnt += 1

                    # rate limit < 1 request/second. Dont rtlm - (start - end)
                    time.sleep(self.config.rtlm)

                except Exception as e:
                    LogException(e, logger=log_etl)
                    cnt += 1
                    continue

            log_etl.info("Extraction: Saving updated data to file")
            save_json(data=city_dict, save_path=save_path)

        except Exception as e:
            LogException(e, logger=log_etl)
            raise CustomException(e)
