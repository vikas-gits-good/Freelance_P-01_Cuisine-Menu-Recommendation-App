import re
from typing import Optional, Dict, List, Any, Literal
from pydantic import BaseModel, model_validator

from src.ETL.Constants.cyphers import NodeLabels, RelationshipLabels

from src.Logging.logger import log_etl
from src.Utils.main_utils import LogException, CustomException


# Restaurant details to scrape from json
class Restaurant(BaseModel):
    """pydantic.BaseModel that returns restaurant details from scraped JSON.

    ## Usage:
    ```python
    >>> rstn = Restaurant(**json_data['data'])
    >>> rstn
    >>> Restaurant(ids=8840, name='Smoke House Deli', city='Delhi', locality='Saket', area='Saket', cuisines=['Pizzas', 'Pastas'], rating=4.2, address='...', coords='28.5286078,77.2160345', chain=True)
    ```
    Attributes:
        ids (int): Unique ID for each restaurants. Default -1.
        name (str): Restaurant name. Default ''.
        city (str): City of restaurant. Default ''.
        area (str): Area of restaurant. Default ''.
        locality (str): Locality of restaurant. Default ''.
        cuisines (List['str']): List of cuisines available. Default [''].
        rating (float): Average customer rating for online ordering. Default -1.0.
        address (str): Physical address of restaurant. Default ''.
        coords (str): Latitude, Longitude coordinates of restaurant. Default ''.
        chain (bool): Is this a restaurant chain? Default False.

    Returns:
        Restaurant (BaseModel): A class object with variables as details
    """

    ids: int = -1
    name: str = ""
    city: str = ""
    area: str = ""
    locality: str = ""
    cuisines: List[str] = [""]
    rating: float | None = None
    address: str = ""
    coords: List[float] | None = None
    chain: bool = False
    city_id: str = ""
    # include number of ratings as well

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
            if (rating := main_part["info"].get("avgRating", ""))
            else None,
            "address": main_part["info"]["labels"][1].get("message", "").strip(),
            "coords": [float(x) for x in latlong.split(",")]
            if (latlong := main_part["info"].get("latLong", "").strip())
            else None,
            "chain": main_part["info"].get("multiOutlet", False),
            "city_id": re.sub(
                r"[,-_]+", " ", main_part["info"]["slugs"].get("city", "")
            ).strip(),
        }
        return clean_data

    def to_node_dict(self):
        clean_data = {
            "ids": self.ids,
            "params": {
                "name": self.name,
                "city": self.city,
                "area": self.area,
                "locality": self.locality,
                "cuisines": self.cuisines,
                "rating": self.rating,
                "address": self.address,
                "coords": self.coords,
                "chain": self.chain,
                "city_id": self.city_id,
            },
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
            "price": round(int(price) / 100)
            if (price := main_part.get("price", ""))
            else None,
            "rating": float(rating)
            if (rating := main_part["ratings"]["aggregatedRating"].get("rating", ""))
            else None,
            "types": _types,
        }
        return clean_data


# Main class to process menu
class Menu(BaseModel):
    """Pydantic.BaseModel class that returns a list of food items.

    ## Usage:
    ```python
    >>> menu = Menu(**json_data['data'])
    >>> menu.food_items
    >>> [
    FoodItem(ids='146696388', name='Pink Pasta Feast Box', category='Premium Feast Boxes', description='pasta ...', price='Rs.450', types='VEG', rating=3.8),
    FoodItem(ids='146696386', name='Cottage Cheese Steak Box', category='Premium Feast Boxes', description='cheese steak ...', price='Rs.450', types='VEG', rating=4.4)
    ]
    ```

    Returns:
        Menu (List[FoodItem]): List of `FoodItem` class with food details
    """

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

    def to_node_dict(self) -> List[Dict[str, Any]]:
        part_food = []
        for food in self.food_items:
            data = {
                "name": food.name,
                "params": {
                    "types": food.types,
                },
            }
            part_food.append(data)
        return part_food


class BaseLocation(BaseModel):
    """Base model with common attributes for all location nodes.

    Args:
        ids (str): OpenStreetMap location identification format.
            `Ex: "osm_type:osm_id"`
        name (str): Location name in human readable form.
            `Example: "India", "Assam", 'Davangere'`
        old_name (str): Location name in human readable form.
            `Example: "India", "Assam", 'Davangere'`
        iso_code (Optional[str]): ISO Code for the location.
            `Ex: "IN"`
        coords (Optional[str]): Latitude, Longitude with `,` delimiter.
            `Ex: "19.5670323,76.4164557"`
        boundingbox (Optional[str]): Location enclosing latitude, longitude with `,` delimiter.
            `Ex: "15.6063596,22.0302694,72.6526112,80.8977842"`
    """

    ids: str
    name: str
    old_name: Optional[str] = None
    iso_code: Optional[str] = None
    coords: Optional[str] = None
    boundingbox: Optional[str] = None

    @classmethod
    def substitute(cls, strn, subs):
        return re.sub(r"[ _,]+", subs, strn).strip()

    def to_node_dict(self):
        clean_data = {
            "ids": self.ids,
            "params": {
                "name": self.name,
                "old_name": self.old_name,
                "iso_code": self.iso_code,
                "coords": self.coords,
                "boundingbox": self.boundingbox,
            },
        }
        return clean_data


class Country(BaseLocation):
    """Model for `Country` node.

    Args:
        ids (str): OpenStreetMap location identification format.
            `Ex: "osm_type:osm_id"`
        name (str): Location name in human readable form.
            `Example: "India"`
        iso_code (Optional[str]): ISO Code for the location.
            `Ex: "IN"`
        coords (Optional[str]): Latitude, Longitude with `,` delimiter.
            `Ex: "19.5670323,76.4164557"`
        boundingbox (Optional[str]): Location enclosing latitude, longitude with `,` delimiter.
            `Ex: "15.6063596,22.0302694,72.6526112,80.8977842"`
    """

    pass


class State(BaseLocation):
    """Model for `State` node.

    Args:
        ids (str): OpenStreetMap location identification format.
            `Ex: "osm_type:osm_id"`
        name (str): Location name in human readable form.
            `Example: "Assam"`
        iso_code (Optional[str]): ISO Code for the location.
            `Ex: "IN-AS"`
        coords (Optional[str]): Latitude, Longitude with `,` delimiter.
            `Ex: "19.5670323,76.4164557"`
        boundingbox (Optional[str]): Location enclosing latitude, longitude with `,` delimiter.
            `Ex: "15.6063596,22.0302694,72.6526112,80.8977842"`
    """

    pass


class City(BaseLocation):
    """Model for `City` node.

    Args:
        ids (str): OpenStreetMap location identification format.
            `Ex: "osm_type:osm_id"`
        name (str): Location name in human readable form.
            `Example: "Assam"`
        iso_code (Optional[str]): ISO Code for the location.
            `Ex: "IN-AS"`
        coords (Optional[str]): Latitude, Longitude with `,` delimiter.
            `Ex: "19.5670323,76.4164557"`
        boundingbox (Optional[str]): Location enclosing latitude, longitude with `,` delimiter.
            `Ex: "15.6063596,22.0302694,72.6526112,80.8977842"`
    """

    pass


class Area(BaseLocation):
    """Model for `Area` node.

    ## Usage:
    ```python
    >>> from src.ETL.Config import Restaurant
    >>> rstn = Restaurant(**json_data['data'])
    >>> city_id = city_json['id'] # <- double check this
    >>> area = Area.from_data((city_id, rstn))
    >>> area
    Area(
        ids='area_Koramangala__city_Bengaluru-relation:7902476',
        name='Koramangala',
        iso_code = None,
        coords = None,
        boundingbox = None,
    )
    ```

    Args:
        ids (str): Unique id derive from area and city.
            `Ex: "area_Koramangala__city_Bengaluru-relation:7902476"`
        name (str): Location name in human readable form.
            `Example: "Koramangala"`
        iso_code (Optional[str]): ISO Code for the location.
            `Ex: "IN-KA"`
        coords (Optional[str]): Latitude, Longitude with `,` delimiter.
            `Ex: "19.5670323,76.4164557"`
        boundingbox (Optional[str]): Location enclosing latitude, longitude with `,` delimiter.
            `Ex: "15.6063596,22.0302694,72.6526112,80.8977842"`
    """

    @model_validator(mode="before")
    @classmethod
    def ent(cls, data: Dict[str, Any]):
        area_name = cls.substitute(data["rstn"].area, "-")
        city_name = cls.substitute(data["rstn"].city, "-")
        city_id = data["city_id"]
        clean_data = {
            "ids": f"area_{area_name}__city_{city_name}-{city_id}",
            "name": cls.substitute(data["rstn"].area, " "),
            "old_name": None,
            "iso_code": None,
            "coords": None,
            "boundingbox": None,
        }
        return clean_data


class Locality(BaseLocation):
    """Model for `Locality` node.

    ## Usage:
    ```python
    >>> from src.ETL.Config import Restaurant
    >>> rstn = Restaurant(**json_data['data'])
    >>> city_id = city_json['id'] # <- double check this
    >>> locality = Locality.from_data((city_id, rstn))
    >>> locality
    >>> Locality(
        ids='locality_5th-Block__area_Koramangala__city_Bengaluru-relation:7902476',
        name='5th Block',
        iso_code = None,
        coords = None,
        boundingbox = None,
    )
    ```

    Args:
        ids (str): Unique id derive from locality, area and city.
            `Ex: "locality_5th-Block__area_Koramangala__city_Bengaluru-relation:7902476"`
        name (str): Location name in human readable form.
            `Example: "5th Block"`
        iso_code (Optional[str]): ISO Code for the location.
            `Ex: "IN-AS"`
        coords (Optional[str]): Latitude, Longitude with `,` delimiter.
            `Ex: "19.5670323,76.4164557"`
        boundingbox (Optional[str]): Location enclosing latitude, longitude with `,` delimiter.
            `Ex: "15.6063596,22.0302694,72.6526112,80.8977842"`
    """

    @model_validator(mode="before")
    @classmethod
    def ent(cls, data: Dict[str, Any]):
        area_name = cls.substitute(data["rstn"].area, "-")
        lclt_name = cls.substitute(data["rstn"].locality, "-")
        city_name = cls.substitute(data["rstn"].city, "-")
        city_id = data["city_id"]
        clean_data = {
            "ids": f"locality_{lclt_name}__area_{area_name}__city_{city_name}-{city_id}",
            "name": cls.substitute(data["rstn"].locality, " "),
            "old_name": None,
            "iso_code": None,
            "coords": None,
            "boundingbox": None,
        }
        return clean_data


class Cuisine(BaseModel):
    name: str


class MainCuisine(BaseModel):
    cuis: list[str]
    # main_cuisines: List[Cuisine]
    # create these cuisines manually later from Wikipedia

    def to_node_dict(self) -> List[Dict[str, Any]]:
        return [{"name": item, "params": {}} for item in self.cuis]


class SubCuisine(BaseModel):
    cuis: list[str]
    # main_cuisines: List[Cuisine]
    # create these cuisines manually later from Wikipedia

    def to_node_dict(self) -> List[Dict[str, Any]]:
        return [{"name": item, "params": {}} for item in self.cuis]


class RelationshipParams(BaseModel):
    source_ids: str | int
    target_ids: str | int
    source_label: str
    target_label: str
    relationship: str
    params: dict

    @classmethod
    def from_data(
        cls,
        data: dict,
        types: RelationshipLabels,
        item: Any = "",
    ) -> Dict[str, Any]:
        clean_data = {
            "source_ids": "",
            "target_ids": "",
            "source_label": "",
            "target_label": "",
            "relationship": "",
            "params": {},
        }
        try:
            if types == RelationshipLabels.HAS_STATE:
                clean_data = {
                    "source_ids": data["country_lookup"]
                    .get(item["country"], {})
                    .get("ids", ""),
                    "target_ids": item["ids"],
                    "source_label": NodeLabels.COUNTRY.value,
                    "target_label": NodeLabels.STATE.value,
                    "relationship": types.value,
                    "params": {},
                }
            elif types == RelationshipLabels.HAS_CITY:
                clean_data = {
                    "source_ids": data["state_lookup"]
                    .get(item["state"], {})
                    .get("ids", ""),
                    "target_ids": item["ids"],
                    "source_label": NodeLabels.STATE.value,
                    "target_label": NodeLabels.CITY.value,
                    "relationship": types.value,
                    "params": {},
                }
            elif types == RelationshipLabels.HAS_AREA:
                clean_data = {
                    "source_ids": data["city_id"],
                    "target_ids": data["area_dict_node"]["ids"],
                    "source_label": NodeLabels.CITY.value,
                    "target_label": NodeLabels.AREA.value,
                    "relationship": types.value,
                    "params": {},
                }

            elif types == RelationshipLabels.HAS_LOCALITY:
                clean_data = {
                    "source_ids": data["area_dict_node"]["ids"],
                    "target_ids": data["lclt_dict_node"]["ids"],
                    "source_label": NodeLabels.AREA.value,
                    "target_label": NodeLabels.LOCALITY.value,
                    "relationship": types.value,
                    "params": {},
                }

            elif types == RelationshipLabels.HAS_RESTAURANT:
                clean_data = {
                    "source_ids": data["lclt_dict_node"]["ids"],
                    "target_ids": data["rstn"].ids,
                    "source_label": NodeLabels.LOCALITY.value,
                    "target_label": NodeLabels.RESTAURANT.value,
                    "relationship": types.value,
                    "params": {},
                }

            elif types == RelationshipLabels.HAS_MENU:
                clean_data = {
                    "source_ids": data["rstn"].ids,
                    "target_ids": item.name,
                    "source_label": NodeLabels.RESTAURANT.value,
                    "target_label": NodeLabels.MENU.value,
                    "relationship": types.value,
                    "params": {"price": item.price, "rating": item.rating},
                }

            elif types == RelationshipLabels.SERVES_MAIN_CUISINE:
                clean_data = {
                    "source_ids": data["rstn"].ids,
                    "target_ids": item,
                    "source_label": NodeLabels.RESTAURANT.value,
                    "target_label": NodeLabels.MAINCUISINE.value,
                    "relationship": types.value,
                    "params": {},
                }

            elif types == RelationshipLabels.SERVES_SUB_CUISINE:
                pass

            else:
                pass

        except Exception as e:
            LogException(e, logger=log_etl)
            # raise CustomException(e)

        return clean_data
