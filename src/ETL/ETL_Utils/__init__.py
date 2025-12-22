import pandas as pd
from typing import Dict, Any
from crawl4ai.async_webcrawler import AsyncWebCrawler

from src.ETL.ETL_Constants import SwiggyRestaurantConstants
from src.Utils.main_utils import save_json, read_json, save_dataframe
from src.Logging.logger import log_etl
from src.Exception.exception import LogException, CustomException


class RestaurantData:
    def __init__(self, save_path: str, use_proxy_rotation: bool = False) -> None:
        try:
            self.save_path = save_path
            self.use_proxy_rotation = use_proxy_rotation

        except Exception as e:
            LogException(e, logger=log_etl)
            raise CustomException(e)

    async def get(self) -> pd.DataFrame:
        clean_data = pd.DataFrame({"data": ["Error in RestaurantData().get()"]})
        try:
            json_data = await self._get_json_data()
            clean_data = self._get_clean_data(json_data)

        except Exception as e:
            LogException(e, logger=log_etl)
            raise CustomException(e)

        return clean_data

    async def _get_json_data(self) -> Dict[str, Any]:
        json_data = {"data": "Error in RestaurantData()._get_json_data()"}
        try:
            api_endpoint = SwiggyRestaurantConstants.SWIGGY_API_ENDPOINT
            save_path_json = SwiggyRestaurantConstants.JSON_FILE_SAVE_PATH

            # you need to format the 'save_path_json' with lat, long, qry params
            save_json(data=json_data, save_path=save_path_json)

        except Exception as e:
            LogException(e, logger=log_etl)
            raise CustomException(e)

        return json_data

    def _get_clean_data(self, data) -> pd.DataFrame:
        clean_data = pd.DataFrame(
            {"data": ["Error in RestaurantData()._get_clean_data()"]}
        )
        try:
            if data["data"]["statusMessage"] in ["done successfully"]:
                save_path_df = SwiggyRestaurantConstants.DF_FILE_SAVE_PATH
                ...

                # you need to format the 'save_path_df' with lat, long, qry params
                save_dataframe(data=clean_data, save_path=save_path_df)
            else:
                log_etl.info("Extraction: JSON statusMessage != 'Success'")

        except Exception as e:
            LogException(e, logger=log_etl)
            raise CustomException(e)

        return clean_data
