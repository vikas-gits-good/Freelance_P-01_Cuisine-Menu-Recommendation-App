import os
from typing import Any, Dict, Literal

from dotenv import load_dotenv

from Src.Config import MongoDBConfig, RedisDBConfig
from Src.Constants import MDBIndexKey
from Src.Utils import (
    LogException,
    log_etl,
    pull_from_mongodb,
    upsert_to_mongodb,
    upsert_to_redisdb,
)


class SitemapUploader:
    def __init__(
        self,
        mg_cnf: MongoDBConfig = MongoDBConfig(),
        rd_cnf: RedisDBConfig = RedisDBConfig(),
    ):
        try:
            self.mg_cnf = mg_cnf
            self.rd_cnf = rd_cnf
            load_dotenv(".env")

        except Exception as e:
            LogException(e, logger=log_etl)

    def upsert_mongo(self, data: Dict[str, Any]):
        """Method to upsert data into mongodb"""
        # Before upserting, get old data so that you only queue missing
        # urls to Redis Cache
        log_etl.info("Seeder: Filtering out currently available urls from failed urls")
        prev_data = pull_from_mongodb(  # old urls
            database=self.mg_cnf.swiggy.database,
            collection=self.mg_cnf.swiggy.coll_rstn_cnfg,
            idx_key=MDBIndexKey.RESTAURANT_CITY,
            city=os.getenv("SEEDER_CITY", "bangalore"),
            limit=0,
            prefix="Seeder",
        )
        fail_data = pull_from_mongodb(  # failed urls
            database=self.mg_cnf.swiggy.database,
            collection=self.mg_cnf.swiggy.coll_upst_fail,
            idx_key=MDBIndexKey.RESTAURANT_CITY,
            city=os.getenv("SEEDER_CITY", "bangalore"),
            limit=0,
            prefix="Seeder",
        )

        self.old_data = {}  # old urls that succeeded
        for _city in prev_data.keys():
            all_urls = {rstn["rstn_url"] for rstn in prev_data[_city]["restaurants"]}
            fail_urls = {rstn["url"] for rstn in fail_data[_city]}
            self.old_data[_city] = {
                "restaurants": [{"rstn_url": url} for url in (all_urls - fail_urls)],
            }

        log_etl.info("Seeder: Upserting new links to MongoDB")
        upsert_to_mongodb(
            data=data,
            database=self.mg_cnf.swiggy.database,
            collection=self.mg_cnf.swiggy.coll_rstn_cnfg,
            idx_key=MDBIndexKey.RESTAURANT_CITY,
        )

    def upsert_redis(self):
        """Method to upsert data into redis

        Args:
            purpose (Literal["full", "ltst"]): upsert all urls or only latest urls
        """
        try:
            log_etl.info("Seeder: Getting updated urls to queue from MongoDB")
            # DO NOT remove this and use data from upsert_mongo()
            city_data = pull_from_mongodb(
                database=self.mg_cnf.swiggy.database,
                collection=self.mg_cnf.swiggy.coll_rstn_cnfg,
                idx_key=MDBIndexKey.RESTAURANT_CITY,
                city=os.getenv("SEEDER_CITY", "bangalore"),
            )

            log_etl.info("Seeder: Filtering urls")  # {"city": {"name": {...}}}
            city_data = self._filter_data(
                new_data=city_data,
                purpose=os.getenv("SEEDER_PURPOSE", "ltst"),
            )

            log_etl.info("Seeder: Putting urls to RedisDB queue")
            upsert_to_redisdb(city_data)

        except Exception as e:
            LogException(e, logger=log_etl)

    def _filter_data(
        self,
        new_data: Dict[str, Any],
        purpose: Literal["full", "ltst"] = "full",
    ) -> Dict[str, Any]:
        filt_data = new_data
        try:
            if purpose == "full":
                filt_data = new_data

            elif purpose == "ltst":
                filt_data = {}
                for city, data in new_data.items():
                    try:
                        old_urls = {
                            rstn["rstn_url"]
                            for rstn in self.old_data[city]["restaurants"]
                        }
                        all_urls = {rstn["rstn_url"] for rstn in data["restaurants"]}
                        filt_data[city] = {
                            "restaurants": [
                                {"rstn_url": url} for url in list(all_urls - old_urls)
                            ],
                        }

                    except Exception as e:
                        LogException(e, logger=log_etl)
                        continue

        except Exception as e:
            LogException(e, logger=log_etl)

        return filt_data
