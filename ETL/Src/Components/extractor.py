import os

from dotenv import load_dotenv

from Src.Config import ScrapeConfig
from Src.Scraper import RestaurantDataScraper
from Src.Utils import LogException, log_etl


class ETL_Scraper:
    def __init__(self):
        try:
            load_dotenv(".env")
            self.batch_size = int(os.getenv("SCRAPER_BATCH_SIZE", "100"))
            self.scrp_confg = ScrapeConfig(
                max_parallel=int(os.getenv("SCRAPER_PARALLEL", "10"))
            )

        except Exception as e:
            LogException(e, logger=log_etl)

    def run(self):
        try:
            log_etl.info("Extraction: Initialising scraping")
            rstn_drsp = RestaurantDataScraper(self.batch_size, self.scrp_confg)

            log_etl.info("Extraction: Starting restaurant data scraping")
            rstn_drsp.get()

        except Exception as e:
            LogException(e, logger=log_etl)
