import re
from typing import Any, Dict, List, Literal

from pydantic import BaseModel, model_validator


## Restaurant data from scraped json_data
class Restaurant(BaseModel):
    """pydantic.BaseModel that returns restaurant details from scraped JSON."""

    ids: int = -1
    name: str = ""
    city: str = ""
    area: str = ""
    locality: str = ""
    cuisines: List[str] = [""]
    rating: float | None = None
    address: str = ""
    coords: str = ""
    chain: bool = False
    city_id: str = ""

    @model_validator(mode="before")
    @classmethod
    def extract_and_transform(cls, data):
        main_part = data["cards"][2]["card"]["card"]
        clean_data = {
            "ids": int(main_part["info"].get("id", "-1")),
            "name": main_part["info"].get("name", "").strip(),
            "city": main_part["info"].get("city", "").strip(),
            "area": main_part["info"].get("areaName", "").strip(),
            "locality": main_part["info"]
            .get("locality", main_part["info"].get("areaName", ""))
            .strip(),
            "cuisines": main_part["info"].get("cuisines", [""]),
            "rating": float(rating)
            if (rating := main_part["info"].get("avgRating")) is not None
            else None,
            "address": main_part["info"]["labels"][1].get("message", "").strip(),
            "coords": main_part["info"].get("latLong", "").strip(),
            "chain": main_part["info"].get("multiOutlet", False),
            "city_id": re.sub(
                r"[-_]", " ", main_part["info"]["slugs"].get("city", "")
            ).strip(),
        }
        return clean_data


# Menu has multiple categories called cards
class MenuCards(BaseModel):
    menu_card_list: List[Dict[str, Any]]

    # select a list of cards
    @model_validator(mode="before")
    @classmethod
    def extract_and_transform(cls, data):
        menu_cards = data["cards"][4]["groupedCard"]["cardGroupMap"]["REGULAR"][
            "cards"
        ][1:]
        return {"menu_card_list": menu_cards}

    # filter out the cards thats not needed
    @model_validator(mode="after")
    def filter_valid_cards(self):
        filtered_cards = [
            card
            for card in self.menu_card_list
            if card.get("card", {}).get("card", {}).get("@type", "").split(".")[-1]
            in ["ItemCategory", "NestedItemCategory"]
        ]
        self.menu_card_list = filtered_cards
        return self


# There are multiple items in each menu card category
class MenuItemsList(BaseModel):
    menu_items_list: List[Dict[str, Any]]

    @model_validator(mode="before")
    @classmethod
    def extract_and_transform(cls, data):
        # ItemCategory
        if "itemCards" in list(data["card"]["card"].keys())[2]:
            menu_items = data["card"]["card"]["itemCards"]

        # NestedItemCategory
        elif "categories" in list(data["card"]["card"].keys())[2]:
            categories = data["card"]["card"]["categories"]
            menu_items = [item for catg in categories for item in catg["itemCards"]]

        # Error
        else:
            menu_items = [{}]

        return {"menu_items_list": menu_items}


# The actual food item
class FoodItem(BaseModel):
    # ids: str = "" # leave this out.
    name: str = ""
    category: str = ""
    description: str = ""
    price: int | None = None
    rating: float | None = None
    types: Literal["VEG", "NONVEG", "EGG", "UNKNOWN"] = "UNKNOWN"
    cuisine: str = ""  # make subcuisine later, maincuisine now

    @model_validator(mode="before")
    @classmethod
    def extract_and_transform(cls, data):
        main_part = data["card"]["info"]
        valid_types = {"VEG", "NONVEG", "EGG"}
        if "itemAttribute" in main_part:
            _types = main_part["itemAttribute"].get("vegClassifier", "UNKNOWN").strip()
        else:
            _types = next(
                (t for t in main_part.get("menuFilterIds", []) if t in valid_types),
                "UNKNOWN",
            )

        clean_data = {
            # "ids": main_part.get("id", ""),
            "name": main_part.get("name", "").strip(),
            "category": main_part.get("category", "").strip(),
            "description": main_part.get("description", "").strip(),
            "price": round(int(price))
            if (price := main_part.get("price")) is not None
            else None,
            "rating": float(rating)
            if (rating := main_part["ratings"]["aggregatedRating"].get("rating"))
            is not None
            else None,
            "types": _types,
        }
        return clean_data


# Main class to process menu
class Menu(BaseModel):
    """Pydantic.BaseModel class that returns a list of food items."""

    food_items: List[FoodItem]

    @model_validator(mode="before")
    @classmethod
    def extract_and_transform(cls, data):
        menu_cards_list = MenuCards(**data)
        menu_items_list = [
            MenuItemsList(**menu_card) for menu_card in menu_cards_list.menu_card_list
        ]
        food_list = [
            FoodItem(**mi)
            for menu_item in menu_items_list
            for mi in menu_item.menu_items_list
        ]

        return {"food_items": food_list}
