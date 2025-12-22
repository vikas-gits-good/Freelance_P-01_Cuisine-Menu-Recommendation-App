from dataclasses import dataclass


@dataclass
class SwiggyRestaurantConstants:
    SWIGGY_API_ENDPOINT = "https://www.swiggy.com/dapi/restaurants/search/v3?lat={latitude}&lng={longitude}&str={query}&submitAction=ENTER"
    JSON_FILE_SAVE_PATH = (
        "src/ETL/ETL_Data/json_data_{latitude}_{longitude}_{query}.json"
    )
    DF_FILE_SAVE_PATH = "src/ETL/ETL_Data/df_data_{latitude}_{longitude}_{query}.pkl"


@dataclass
class 