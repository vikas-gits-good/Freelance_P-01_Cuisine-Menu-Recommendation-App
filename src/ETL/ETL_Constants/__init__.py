from dataclasses import dataclass
from src.Utils.main_utils import read_json


@dataclass
class SwiggyRestaurantConstants:
    SWIGGY_API_ENDPOINT = "https://www.swiggy.com/dapi/restaurants/search/v3?lat={latitude}&lng={longitude}&str={query}&submitAction=ENTER"
    JSON_FILE_SAVE_PATH = "src/ETL/ETL_Data/json_data.json"
    DF_FILE_SAVE_PATH = "src/ETL/ETL_Data/df_data.pkl"
    COORDINATES_JSON = read_json(save_path="src/ETL/ETL_Constants/coordinates.json")
    DISTANCE = 10
    QUERIES = [
        f"All eateries within {DISTANCE}km range",
        f"Nearby restaurants in {DISTANCE}km",
        f"Restaurants {DISTANCE}km radius around",
        f"Dining spots in {DISTANCE}km circle",
        f"All food joints {DISTANCE}km nearby",
        f"Eateries within {DISTANCE}km distance",
        f"{DISTANCE}km radius all restaurants",
        f"Local restaurants {DISTANCE}km area",
        f"Food places in {DISTANCE}km",
        f"All dining {DISTANCE}km vicinity",
        f"Restaurants near me {DISTANCE}km",
        f"{DISTANCE}km all food outlets",
        f"Nearby eateries {DISTANCE}km radius",
        f"Dining options {DISTANCE}km range",
        f"All restaurants within {DISTANCE}km",
        f"Food spots {DISTANCE}km circle",
        f"{DISTANCE}km nearby all eateries",
        f"Restaurants in {DISTANCE}km zone",
        f"Local dining {DISTANCE}km radius",
        f"All food venues {DISTANCE}km",
    ]
