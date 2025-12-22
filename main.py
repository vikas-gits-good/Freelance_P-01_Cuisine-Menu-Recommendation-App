import json
import pandas as pd
from urllib.parse import quote
from dataclasses import dataclass

import asyncio


path = "src/Research/all_restaurants.json"

with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)


restaurant_list: list[dict] = data["data"]["cards"][1]["groupedCard"]["cardGroupMap"][
    "RESTAURANT"
]["cards"]


restaurant_data = []
for card in restaurant_list:
    info = card["card"]["card"]["info"]
    try:
        restaurant_data.append(
            {
                "restaurant_id": int(info["id"]),
                "restaurant_name": info["name"],
                # "restaurant_url": f"https://www.swiggy.com/restaurants/{quote(info['slugs']['restaurant'])}-{info['id']}/dineout",
                "city": info["slugs"]["city"],
                "address": info["address"],
                "locality": info["locality"],
                "area": info["areaName"],
                "cuisines": ", ".join([item for item in info["cuisines"]]),
                "average_rating": float(info.get("avgRating", "-1.0")),
            }
        )
    except Exception as e:
        print(f"Restaurant {info['name']}. Error: {e}")
        continue


df = pd.DataFrame(restaurant_data)
df.to_pickle("src/Research/restaurant_data.pkl")


@dataclass
class SwiggyRestaurantConstants:
    SWIGGY_API_ENDPOINT = "https://www.swiggy.com/dapi/restaurants/search/v3?lat={latitude}&lng={longitude}&str={query}&submitAction=ENTER"
    JSON_FILE_SAVE_PATH = "src/Research/all_restaurants.json"


class RestaurantData:
    def __init__(self, save_path: str) -> None:
        self.save_path = save_path

    def get(self) -> pd.DataFrame:
        try:
            json_data = self._get_json_data()
            clean_data = self._get_clean_data()

        except Exception as e:
            print(f"Error: {e}")
            raise e
