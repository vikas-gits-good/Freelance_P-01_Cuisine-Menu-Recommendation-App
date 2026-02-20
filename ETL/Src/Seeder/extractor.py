import asyncio
import gzip
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Tuple

import httpx

from Src.Config import MongoDBConfig
from Src.Constants import MDBIndexKey
from Src.Utils import LogException, log_etl, pull_from_mongodb, upsert_to_mongodb


class SitemapExtractor:
    """Lightweight class method to seed urls to mongodb and redis"""

    RE_LOC = re.compile(rb"<loc>([^<]+)</loc>")
    RE_SITEMAP_TAG = re.compile(rb"<sitemap[>\s]")
    RE_ROBOTS_SITEMAP = re.compile(
        r"\[?https://www\.swiggy\.com/sitemap\.xml\.gz\]?",
        re.MULTILINE | re.IGNORECASE,
    )
    RE_CLEAN_CITY = re.compile(r"[,\-_]+")

    def __init__(
        self,
        website: str,
        pattern: re.Pattern,
        headers: str,
        threads: int = 4,
        max_con: int = 10,
        mg_cnf: MongoDBConfig = MongoDBConfig(),
    ):
        """Lightweight sitemap extractor. Async I/O for downloads, multithreaded for decompression + regex.

        Args:
            website (str): Website whose sitemap to get.
            pattern (re.Pattern): regex pattern to filter sitemap urls.
            headers (str): HTTP request header.
            threads (int): Number of parallel processing workers. Default 4.
            max_connections (int): The maximum number of concurrent connections that may be established. Default 10.

        Returns:
            city_data (Dict[str, Dict[str, Any]]): Dictionary containing restaurant id and urls sorted by city.

        Usage:
        ```python
        >>> from Src.Utils import get_seeder_info
        >>> extractor = SitemapExtractor(*get_seeder_info())
        >>> city_data = asyncio.run(extractor.extract())
        >>> city_data
        >>> {
            "abohar": {
                "restaurants": [
                    {
                        "rstn_id": 156588,
                        "rstn_url: "https://www.swiggy.com/city/abohar/shere-punjab-veg-surinder-chowk-kishna-nagri-rest156588",
                    },
                    ...
                ]
            },
            ...
        }
        ))
        ```
        """
        try:
            self.website = website.rstrip("/")
            self.pattern = re.compile(pattern)
            self.headers = {"User-Agent": headers} or {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }
            self.max_connections = max_con
            self.max_workers = threads
            self.mg_cnf = mg_cnf
            self.city_data = pull_from_mongodb(
                database=self.mg_cnf.swiggy.database,
                collection=self.mg_cnf.swiggy.coll_uq_ct_ids,
                idx_key=MDBIndexKey.UNIQUE_CITY,
                city="all",
                limit=0,
                prefix="Seeder",
            )

        except Exception as e:
            LogException(e, logger=log_etl)

    async def extract(self) -> Dict[str, Any]:
        """Main entry. Returns list of decoded regex match groups from all sitemap URLs."""
        city_data = {}
        try:
            limits = httpx.Limits(
                max_connections=self.max_connections,
                max_keepalive_connections=self.max_connections,
            )

            async with httpx.AsyncClient(
                headers=self.headers, timeout=30, limits=limits, follow_redirects=True
            ) as client:
                self._client = client

                # 1. Discover sitemap URLs from robots.txt
                sitemap_urls = await self._get_sitemap_urls()

                # 2. Recursively fetch + process all sitemaps
                matched_data = await self._fetch_and_process(sitemap_urls, self.pattern)

                # 3. Create dictionary using this data.
                city_data, miss_data = self._create_dict(matched_data, self.city_data)

                log_etl.info("Seeder: Preparing to upsert missing cities to MongoDB")
                miss_data = dict(sorted(miss_data.items()))
                upsert_to_mongodb(
                    data=miss_data,
                    database=self.mg_cnf.swiggy.database,
                    collection=self.mg_cnf.swiggy.coll_ms_ct_nam,
                    idx_key=MDBIndexKey.UNIQUE_CITY,
                )

                city_data = dict(sorted(city_data.items()))

        except Exception as e:
            LogException(e, logger=log_etl)

        return city_data

    async def _get_sitemap_urls(self) -> List[str]:
        """Fetch robots.txt and extract Sitemap: lines."""
        try:
            resp = await self._client.get(f"https://{self.website}/robots.txt")

            if resp.status_code != 200:
                # Fallback: try common sitemap locations
                return [
                    f"https://{self.website}/sitemap.xml.gz",
                ]

            urls = self.RE_ROBOTS_SITEMAP.findall(resp.text)
            data = (
                [u.strip() for u in urls]
                if urls
                else [f"https://{self.website}/sitemap.xml.gz"]
            )

        except Exception as e:
            LogException(e, logger=log_etl)

        return data

    async def _fetch_and_process(
        self, urls: list[str], pattern: re.Pattern
    ) -> List[Tuple]:
        """Recursively fetch sitemaps. Threaded decompression + regex per file."""
        try:
            all_matches = []
            loop = asyncio.get_running_loop()

            while urls:
                try:
                    # Fetch all current-level sitemaps concurrently
                    responses = await asyncio.gather(
                        *[self._client.get(url) for url in urls],
                        return_exceptions=True,
                    )

                    # Decompress + regex each file in thread pool
                    next_urls = []
                    with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
                        try:
                            futures = []
                            for url, resp in zip(urls, responses):
                                log_etl.info(f"Seeder: Found url: '{url}'")

                                if (
                                    isinstance(resp, Exception)
                                    or resp.status_code != 200
                                ):
                                    continue

                                futures.append(
                                    loop.run_in_executor(
                                        pool,
                                        self._process_one,
                                        resp.content,
                                        url,
                                        pattern,
                                    )
                                )

                            results = await asyncio.gather(*futures)

                        except Exception as e:
                            LogException(e, logger=log_etl)

                    for child_urls, matches in results:
                        next_urls.extend(child_urls)
                        all_matches.extend(matches)

                    urls = next_urls  # Recurse into any discovered sitemap indexes

                except Exception as e:
                    LogException(e, logger=log_etl)
                    continue

        except Exception as e:
            LogException(e, logger=log_etl)

        return all_matches

    @staticmethod
    def _process_one(
        content: bytes, url: str, pattern: re.Pattern
    ) -> Tuple[List[str], List[Tuple]]:
        """One sitemap file: decompress → detect index vs urlset → regex extract.
        Runs in thread pool. Returns (child_sitemap_urls, matched_tuples)."""
        try:
            xml_bytes = gzip.decompress(content) if url.endswith(".gz") else content

            # Sitemap index → extract child sitemap URLs, no pattern matching
            if SitemapExtractor.RE_SITEMAP_TAG.search(xml_bytes[:2048]):
                child_urls = [
                    loc.decode() for loc in SitemapExtractor.RE_LOC.findall(xml_bytes)
                ]
                return child_urls, []

            # Regular sitemap → apply user's pattern, decode matched groups
            xml_str = xml_bytes.decode("utf-8", "ignore")
            matches = [tuple(g for g in m.groups()) for m in pattern.finditer(xml_str)]

        except Exception as e:
            LogException(e, logger=log_etl)

        return [], matches

    @staticmethod
    def _create_dict(
        data: List[Tuple],
        unq_data: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Method to take extracted url data and convert to required format

        Args:
            data (List[Tuple]): Extracted url, city, rstn_id data
            unq_data (Dict[str, Any]): City related data

        Returns:
            city_data, miss_data (Tuple[Dict[str, Any]): url data in required format
            and city names that are missing from unq_data
        """
        try:
            city_data = {}
            miss_data = set()
            for url, city, rstn_id in data:
                try:
                    city = SitemapExtractor.RE_CLEAN_CITY.sub(" ", city).strip()
                    if city not in city_data.keys():
                        if city not in unq_data.keys():
                            miss_data.add(city)

                        city_data[city] = {
                            "ids": unq_data.get(city, {}).get("ids", ""),
                            "name": unq_data.get(city, {})
                            .get("params", {})
                            .get("name", ""),
                            "old_name": unq_data.get(city, {})
                            .get("params", {})
                            .get("old_name", ""),
                            "coords": unq_data.get(city, {})
                            .get("params", {})
                            .get("coords", [0, 0]),
                            "boundingbox": unq_data.get(city, {})
                            .get("params", {})
                            .get("boundingbox", [0, 0, 0, 0]),
                            "state": unq_data.get(city, {}).get("state", ""),
                            "country": unq_data.get(city, {}).get("country", ""),
                            "restaurants": [],
                        }

                    city_data[city]["restaurants"].append(
                        {"rstn_id": int(rstn_id), "rstn_url": url}
                    )

                except Exception as e:
                    LogException(e, logger=log_etl)
                    continue

            log_etl.info(
                f"Seeder: These cities were missing from 'unq_ids_city.json'\n{miss_data}"
            )
            miss_data = {city: {} for city in list(miss_data)}

        except Exception as e:
            LogException(e, logger=log_etl)

        return city_data, miss_data
