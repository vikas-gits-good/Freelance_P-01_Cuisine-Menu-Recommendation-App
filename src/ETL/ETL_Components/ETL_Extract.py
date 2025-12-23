import asyncio
from src.ETL.ETL_Utils import AllLinks, RestaurantData

from src.Logging.logger import log_etl
from src.Exception.exception import LogException, CustomException


class Extract:
    def __init__(self) -> None:
        pass

    def run(self):
        try:
            log_etl.info("Extraction: Starting to extract all links from Swiggy")
            _ = AllLinks().get()

            log_etl.info(
                "Extraction: Starting to extract all Restaurants data from Swiggy"
            )
            _ = asyncio.run(RestaurantData(use_proxy_rotation=False).get())

        except Exception as e:
            LogException(e, logger=log_etl)
            raise CustomException(e)
