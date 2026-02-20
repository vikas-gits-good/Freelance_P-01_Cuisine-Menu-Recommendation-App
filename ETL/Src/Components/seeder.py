import asyncio
import os

from dotenv import load_dotenv

from Src.Seeder import SitemapExtractor, SitemapUploader
from Src.Utils import LogException, get_seeder_info, log_etl


class ETL_Seeder:
    """Method to run seeder app for local development"""

    def __init__(self):
        try:
            load_dotenv(".env")
            self.upld_prps = str(os.getenv("ETL_REDIS_PRPS", "ltst"))
            self.stmp_extr = SitemapExtractor(*get_seeder_info())
            self.stmp_upld = SitemapUploader()

        except Exception as e:
            LogException(e, logger=log_etl)

    def run_seeder(self):
        try:
            log_etl.info("Seeder: Preparing to seed urls")
            city_data = asyncio.run(self.stmp_extr.extract())

            log_etl.info("Seeder: Preparing to upsert seed urls to MongoDB")
            self.stmp_upld.upsert_mongo(city_data)

        except Exception as e:
            LogException(e, logger=log_etl)

    def run_upsert(self):
        try:
            log_etl.info("Seeder: Preparing to upsert urls to RedisDB")
            self.stmp_upld.upsert_redis()

        except Exception as e:
            LogException(e, logger=log_etl)
