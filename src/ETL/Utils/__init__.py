import re
import time
import gzip
import json
import asyncio
import requests
from lxml import etree
from pathlib import Path
from typing import Literal
from requests import Response
from urllib.parse import quote
import xml.etree.ElementTree as ET
from math import radians, sin, cos, sqrt, atan2
from crawl4ai.async_webcrawler import AsyncWebCrawler
from concurrent.futures import ThreadPoolExecutor, as_completed


from src.Config import MongoDBConfig
from src.Utils.main_utils import (
    save_json,
    read_json,
    upsert_to_mongodb,
    get_from_mongodb,
)
from src.ETL.Config.models import Restaurant
from src.ETL.Config import (
    LinksConfig,
    CoordsConfig,
    RestaurantConfig,
    ScrapeConfig,
)
from src.Config import MongoDBConfig

from src.Logging.logger import log_etl
from src.Exception.exception import LogException, CustomException


class AllLinks:
    """Class to download and process sitemap.xml and extract > 3M+ urls and then filter only useful ones.

    Usage Example: -
    ```python
    >>> from src.ETL.ETLUtils import AllLinks
    >>> AllLinks().get()
    ```
    This will output a json file to `src/ETL/ETL_Data/sitemap/unique_data.json`.

    Data format:
    ```python
    >>> from src.Utils.main_utils import read_json
    >>> sitemap_json = read_json(save_path = "src/ETL/ETL_Data/sitemap/unique_data.json")
    >>> sitemap_json
    >>> {
            "abohar": {
                "name": "",
                "coords": [],
                "boundingbox": [],
                "address": {},
                "restaurants": [
                    {
                        "rstn_id": 156588,
                        "rstn_url": "https://www.swiggy.com/city/abohar/shere-punjab-veg-surinder-chowk-kishna-nagri-rest156588"
                    },
                    ...
                ]
                "proxy": ""
            },
            ...
    ```
    """

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
                "Extraction: Getting full sitemap of Swiggy! This is a slow process > 40 minutes."
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

                replacements = {
                    "bankabihar": "Banka",
                    "bharabanki": "Barabanki",
                    "bodhan-rural": "Bodhan",
                    "jamkhambhaliya": "Khambhalia",
                    "kendrapada": "Kendrapara",
                    "mokameh-khas": "Mokameh",
                    "mount-abu": "Mount Abu",
                    "niranjanpura": "Niranjanpur",
                    "pinjore-city": "Pinjore",
                    "jjajjar": "Jhajjar",
                    "shirdi-test-1": "Shirdi",
                    "surendranagar-dudhrej": "Surendranagar",
                    "bangalore": "Bengaluru",
                    "-": " ",
                }
                for old, new in replacements.items():
                    text = text.replace(old, new)

                return text

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
                                    "proxy": "",
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
    """Class to update address and coordinates of 750+ cities from `unique_cities.json`.
    Using [Nominatim's Open Street Map](https://nominatim.openstreetmap.org/) strategy
    is slow > 60 minutes. The [Google Maps](https://developers.google.com/maps/documentation/geocoding)
    strategy is not implemented and may not be necessary.

    Usage Example: -
    ```python
    >>> from src.ETL.ETLUtils import CityCoordinates
    >>> CityCoordinates(source='OSM').get()
    ```
    This will output a json file to `src/ETL/ETL_Data/sitemap/city_rstn_coords_data.json`.

    Data format:
    ```python
    >>> from src.Utils.main_utils import read_json
    >>> city_data = read_json(save_path = "src/ETL/ETL_Data/sitemap/city_rstn_coords_data.json")
    >>> city_data
    >>> {
            "abohar": {
                "name": "Abohar, Abohar Tahsil, Fazilka, Punjab, 152116, India",
                "coords": [30.1450543, 74.1956597],
                "boundingbox": [29.9850543, 30.3050543, 74.0356597, 74.3556597],
                "address": {
                    "city": "Abohar",
                    "county": "Abohar Tahsil",
                    "state_district": "Fazilka",
                    "state": "Punjab",
                    "ISO3166-2-lvl4": "IN-PB",
                    "postcode": "152116",
                    "country": "India",
                    "country_code": "in"
                },
                "restaurants": [
                    {
                        "rstn_id": 156588,
                        "rstn_url": "https://www.swiggy.com/city/abohar/shere-punjab-veg-surinder-chowk-kishna-nagri-rest156588"
                    },
                    ...
                ]
                "proxy": "IN-PB-amritsar"
            },
        ...
        }
    ```
    """

    def __init__(
        self,
        task: Literal["all", "coords", "proxy"] = "all",
        source: Literal["OSM", "GMaps"] = "OSM",
        config: CoordsConfig = CoordsConfig(),
    ) -> None:
        self.task = task
        self.config = config
        self.source = source

    def get(self):
        try:
            read_path = self.config.read_unique_data_path
            save_path = self.config.save_unique_data_path
            self.rqst_parm = self.config.request_params

            self.city_dict = read_json(save_path=read_path)

            if self.task in ["all", "coords"]:
                log_etl.info(
                    f"Extraction: Getting {len(list(self.city_dict.keys())):04d} cities' coordinates & address details. This will take > 10 minutes."
                )
                self._add_coords_address()

            if self.task in ["all", "proxy"]:
                log_etl.info("Extraction: Adding city-wise proxy code")
                self.city_dict = self._add_proxy_codes(city_data=self.city_dict)

            log_etl.info("Extraction: Saving updated data to file")
            save_json(data=self.city_dict, save_path=save_path)

            log_etl.info("Extraction: Saving updated data to MongoDB")
            mc = MongoDBConfig()
            upsert_to_mongodb(
                data=self.city_dict,
                database=mc.swiggy.database,
                collection=mc.swiggy.coll_rstn_cnfg,
                prefix="Extraction",
            )

        except Exception as e:
            LogException(e, logger=log_etl)
            raise CustomException(e)

    def _add_coords_address(self):
        cnt = 1
        for city in self.city_dict.keys():
            try:
                rp = {
                    "url": self.rqst_parm["url"].format(
                        query=quote(f"{city} in India")
                    ),
                    "headers": self.rqst_parm["headers"],
                    "timeout": self.rqst_parm["timeout"],
                }

                # make api call
                response = requests.get(**rp)
                if response.status_code == 200:
                    json_data = response.json()

                    if json_data:
                        self.city_dict[city].update(
                            {"name": json_data[0]["display_name"]}
                        )
                        self.city_dict[city].update(
                            {
                                "coords": [
                                    float(json_data[0]["lat"]),
                                    float(json_data[0]["lon"]),
                                ]
                            }
                        )
                        if "address" in json_data[0].keys():
                            self.city_dict[city].update(
                                {"address": json_data[0]["address"]}
                            )
                        self.city_dict[city].update(
                            {
                                "boundingbox": [
                                    float(data) for data in json_data[0]["boundingbox"]
                                ]
                            }
                        )

                    else:
                        log_etl.info(
                            f"Extraction: Coordinates not found for '{city}'. Continuing"
                        )

                if cnt % 100 == 0:
                    log_etl.info(
                        f"Extraction: Completed {cnt:04d} of {len(list(self.city_dict.keys())):04d} urls."
                    )
                    time.sleep(10)

                cnt += 1

                # rate limit < 1 request/second. Dont rtlm - (start - end)
                time.sleep(self.config.rtlm)

            except Exception as e:
                LogException(e, logger=log_etl)
                cnt += 1
                continue

    def _add_proxy_codes(self, city_data):
        try:
            log_etl.info("Extraction: Finding nearest proxy city for major cities")
            city_data = {key.lower(): val for key, val in city_data.items()}
            proxy_data = read_json(save_path=self.config.read_proxy_data_path)

            all_proxy_cities = [
                city for state in proxy_data["states"] for city in state["cities"]
            ]
            city_data_list = list(city_data.keys())
            missing_cities = {}

            for city_a in city_data_list:
                cn_st = city_data[city_a]["address"]["ISO3166-2-lvl4"]
                for city_b in all_proxy_cities:
                    if city_a == city_b:  # direct assignment for same city
                        city_data[city_a]["proxy"] = f"{cn_st}-{city_b}"

                    else:  # a map b/w city and all proxies in same state
                        for state in proxy_data["states"]:
                            if state["code"] == cn_st.split("-")[-1]:
                                missing_cities[city_a] = {
                                    "state_code": cn_st,
                                    "city_coords": city_data[city_a]["coords"],
                                    "proxy_cities": state["coords"],
                                }
            """
            missing_cities = {
                "abohar": {
                    "state_code": "IN-PB",
                    "city_coords": [30.1450543, 74.1956597],
                    "proxy_cities": [
                        {"ludhiana": [30.9090157, 75.851601]},
                        {"phagwara": [31.2206734, 75.7696463]},
                        {"jalandhar": [31.2922312, 75.5678878]},
                        {"amritsar": [31.6356659, 74.8787496]},
                        {"kharar": [30.7488437, 76.6428994]},
                        {"patiala": [30.2092778, 76.3397231]},
                    ],
                },
                ...
            }
            """

            log_etl.info("Extraction: Finding nearest proxy city for minor cities")
            updated_cities = CityCoordinates.find_nearest_city(missing_cities)

            """
            updated_cities = {
                "abohar": {
                    "state_code": "IN-PB",
                    "city_coords": [30.1450543, 74.1956597],
                    "proxy_cities": [
                        {"ludhiana": [30.9090157, 75.851601]},
                        {"phagwara": [31.2206734, 75.7696463]},
                        {"jalandhar": [31.2922312, 75.5678878]},
                        {"amritsar": [31.6356659, 74.8787496]},
                        {"kharar": [30.7488437, 76.6428994]},
                        {"patiala": [30.2092778, 76.3397231]},
                    ],
                    "proxy": "IN-PB-amritsar",
                },
                ...
            }
            """

            for city in updated_cities.keys():
                city_data[city]["proxy"] = updated_cities[city]["proxy"]

            # Theres some spelling mismatch in state codes
            log_etl.info("Extraction: Finding nearest proxy city for remaining cities")
            missing_cities = {}
            proxy_coords = [
                item for state in proxy_data["states"] for item in state["coords"]
            ]

            for city_a in city_data.keys():
                if not city_data[city_a]["proxy"]:
                    missing_cities[city_a] = {
                        "state_code": "IN",  # placeholder
                        "city_coords": city_data[city_a]["coords"],
                        "proxy_cities": proxy_coords,
                    }

            updated_cities = CityCoordinates.find_nearest_city(missing_cities)

            for city in updated_cities.keys():
                p_city = updated_cities[city]["proxy"].split("-")[-1]
                for state in proxy_data["states"]:
                    if p_city in state["cities"]:
                        city_data[city]["proxy"] = f"IN-{state['code']}-{p_city}"

        except Exception as e:
            LogException(e, logger=log_etl)
            raise CustomException(e)

        return city_data

    @staticmethod
    def find_nearest_city(missing_cities):
        for city in missing_cities.keys():
            try:
                m_lat, m_lon = missing_cities[city]["city_coords"]
                c_city = None
                min_distance = float("inf")

                for p_item in missing_cities[city]["proxy_cities"]:
                    for p_city, p_coords in p_item.items():
                        p_lat, p_lon = p_coords
                        distance = CityCoordinates.haversine_distance(
                            m_lat, m_lon, p_lat, p_lon
                        )

                        if distance < min_distance:
                            min_distance = distance
                            c_city = p_city

                missing_cities[city]["proxy"] = (
                    f"{missing_cities[city]['state_code']}-{c_city}"
                )

            except Exception as e:
                log_etl.info(
                    f"Extraction: Error while trying to find the nearest city in {city}"
                )
                LogException(e, logger=log_etl)
                continue

        return missing_cities

    @staticmethod
    def haversine_distance(lat1, lon1, lat2, lon2):
        """Calculate distance between two coordinates on a sphere in kilometers"""
        R = 6371  # Earth's radius

        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return R * c


class RestaurantData:
    """Class Method to scrape actual Restaurant & Menu details.

    Usage Example:-
    ```python
    >>> from src.ETL.ETLUtils import RestaurantData
    >>> data = RestaurantData().get()
    >>> data
    >>> {
            "abohar": {
                "name": "Abohar, Abohar Tahsil, Fazilka, Punjab, 152116, India",
                "coords": [
                    30.1450543,
                    74.1956597
                ],
                "boundingbox": [
                    29.9850543,
                    30.3050543,
                    74.0356597,
                    74.3556597
                ],
                "address": {
                    "city": "Abohar",
                    "county": "Abohar Tahsil",
                    "state_district": "Fazilka",
                    "state": "Punjab",
                    "ISO3166-2-lvl4": "IN-PB",
                    "postcode": "152116",
                    "country": "India",
                    "country_code": "in"
                },
                "restaurants": [
                    {
                        "rstn_id": 156588,
                        "rstn_url": "https://www.swiggy.com/city/abohar/shere-punjab-veg-surinder-chowk-kishna-nagri-rest156588",
                        "rstn_name": "Shere Punjab Veg",
                        "rstn_city": "Abohar",
                        "rstn_locality": "Surinder Chowk",
                        "rstn_area": "Kishna Nagri",
                        "rstn_cuisines": [
                            "Punjabi"
                        ],
                        "rstn_rating": 4.4,
                        "rstn_address": "major surinder chowk near verma sons petrol pump and lic building abohar",
                        "menu": [
                            {
                                "food_id": "171164207",
                                "food_name": "Dal makhani + 4 roti                           ",
                                "food_category": "Super Saver Meals",
                                "food_description": "Dal makhani served with 4 Roti ( Serves 1 )",
                                "food_price": "Rs.250",
                                "food_rating": 4.3,
                                "food_type": "VEG"
                            },
                            {
                                "food_id": "171164216",
                                "food_name": "Palak paneer + 4 roti                           ",
                                "food_category": "Super Saver Meals",
                                "food_description": "Palak Paneer served with 4 Roti ( Serves 1 )",
                                "food_price": "Rs.260",
                                "food_rating": -1.0,
                                "food_type": "VEG"
                            },
                            ...
                        ]
                    },
                    ...
                ]
            },
            ...
        }
    ```
    """

    def __init__(
        self,
        processing: Literal["series", "parallel"] = "parallel",
        threads: int = 8,
        max_parallel: int = 10,
        rt_config: RestaurantConfig = RestaurantConfig(),
        sc_config: ScrapeConfig = ScrapeConfig(),
    ):
        self.processing = processing
        self.threads = threads
        self.rt_config = rt_config
        self.sc_config = sc_config
        self.sc_config.max_parallel = max_parallel

    def get(self):
        try:
            read_path = self.rt_config.read_unique_data_path
            save_path = self.rt_config.save_unique_data_path
            city_data = read_json(save_path=read_path)

            log_etl.info("Extraction: Preparing to get restaurant data.")
            asyncio.run(self._scrape_all_cities(city_data))
            # log_etl.info("Extraction: Saving restaurant & menu data to local")

            # log_etl.info("Extraction: Saving restaurant & menu data to MongoDB")

        except Exception as e:
            LogException(e, logger=log_etl)
            raise CustomException(e)

    async def _scrape_all_cities(self, city_data):
        # self.updated_city_data = city_data
        mc = MongoDBConfig()
        batch_size = 100  # Save every 50 restaurants

        log_etl.info("Extraction: Getting urls to crawl")
        # urls_dict = {
        #     city: [self.updated_city_data[city]["restaurants"][i]["rstn_url"]]
        #     for city in self.updated_city_data.keys()
        #     for i in range(len(self.updated_city_data[city]["restaurants"]))
        # }
        path_1 = "src/ETL/Data/sitemap/city_rstn_coords_data.json"

        city_data = read_json(path_1)
        # self.updated_city_data = city_data

        # city_data = get_from_mongodb(
        #     database=mc.swiggy.database,
        #     collection=mc.swiggy.coll_rstn_menu,
        # )
        # for i, rstn in enumerate(data_dict_1["bengaluru"]["restaurants"]):
        #     if "menu" in rstn.keys():
        #         city_data["bengaluru"]["restaurants"][i] = rstn

        # wait wont this replace the rows where i have data with no data?
        # urls_dict = {
        #     "bengaluru": [
        #         rstn["rstn_url"]
        #         for rstn in city_data["bengaluru"]["restaurants"]
        #         if "menu" not in rstn.keys()
        #     ]
        # }
        from itertools import islice

        data_limit = 2500
        urls = get_from_mongodb(
            database=mc.swiggy.database,
            collection=mc.swiggy.coll_scrp_data,
        )

        # urls_dict = {
        #     "bengaluru": list(
        #         islice(
        #             (
        #                 rstn["rstn_url"]
        #                 for rstn in city_data["bengaluru"]["restaurants"]
        #                 if rstn["rstn_url"].split("-rest")[-1] not in urls.keys()
        #             ),
        #             data_limit,
        #         )
        #     )
        # }

        urls_dict = {
            "bengaluru": [
                rstn["rstn_url"]
                for rstn in city_data["bengaluru"]["restaurants"]
                if int(rstn["rstn_url"].split("-rest")[-1]) not in list(urls.keys())
            ]
        }
        log_etl.info(f"Extraction: urls_dict has {len(urls_dict['bengaluru']):,} urls")

        for city in urls_dict.keys():
            log_etl.info(
                f"Extraction: Scraping menu data from all restaurants in '{city}'"
            )
            count = 0
            batch_json_data = []

            # Process streaming data as it arrives
            async for menu_data, json_data in self._scrape_one_city(urls_dict[city]):
                try:
                    batch_json_data.append(
                        {
                            "rstn_id": menu_data.rstn_id,
                            "config": json_data,
                        }
                    )

                    count += 1

                    # Save to temp file every batch_size restaurants
                    if count % batch_size == 0:
                        log_etl.info(
                            f"Extraction: Saving batch to file ({count} restaurants)"
                        )
                        upsert_to_mongodb(
                            data=batch_json_data,
                            database=mc.swiggy.database,
                            collection=mc.swiggy.coll_scrp_data,
                        )
                        batch_json_data = []

                except Exception as e:
                    LogException(e, logger=log_etl)
                    continue

            # Save final batch and rename temp file to actual file
            log_etl.info(f"Extraction: Saving final batch ({count} total restaurants)")
            upsert_to_mongodb(
                data=batch_json_data,
                database=mc.swiggy.database,
                collection=mc.swiggy.coll_scrp_data,
            )

    async def _scrape_one_city(self, urls):
        try:
            async with AsyncWebCrawler(
                crawler_strategy=self.sc_config.crawler_strat,
                config=self.sc_config.browser_config,
            ) as crawler:
                # 10 parallel crawlers for each city
                results = await crawler.arun_many(
                    urls=urls,
                    config=self.sc_config.run_config_prxy_rot,
                    dispatcher=self.sc_config.mem_ada_dispatcher,
                )

                # rstn_menu_city = []
                async for result in results:
                    try:
                        for r in result.network_requests:
                            # parse string and extract json
                            if r[
                                "event_type"
                            ] == "response" and "/dapi/menu/pl?" in r.get("url", ""):
                                json_data: dict = json.loads(r["body"]["text"])

                                # parse json to extract restaurant and menu details
                                menu_data = self._extract_menu(json_data)
                                yield menu_data, json_data

                    except Exception as e:
                        LogException(e, logger=log_etl)
                        log_etl.info(
                            f"'{result.url}', {result.status_code}, {result.error_message}"
                        )
                        continue

        except Exception as e:
            LogException(e, logger=log_etl)
            raise CustomException(e)

    def _extract_menu(self, json_data):
        return Restaurant(**json_data["data"])
