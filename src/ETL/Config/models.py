from typing import Optional, Tuple, Dict, List, Any, Union
from pydantic import BaseModel, model_validator

from src.ETL.Config import Restaurant, FoodItem
from src.ETL.Constants.cyphers import NodeLabels, RelationshipLabels

from src.Logging.logger import log_etl
from src.Utils.main_utils import LogException, CustomException


class BaseLocation(BaseModel):
    """Base model with common attributes for all location nodes.

    Args:
        ids (str): OpenStreetMap location identification format.
            `Ex: "osm_type:osm_id"`
        name (str): Location name in human readable form.
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
    iso_code: Optional[str] = None
    coords: Optional[str] = None
    boundingbox: Optional[str] = None


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

    @classmethod
    def from_data(cls, data: Tuple[str, Restaurant]):
        area_name = data[-1].area.replace(" ", "-")
        city_name = data[-1].city.replace(" ", "-")
        city_id = data[0]
        clean_data = {
            "ids": f"area_{area_name}__city_{city_name}-{city_id}",
            "name": data[-1].area,
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

    @classmethod
    def from_data(cls, data: Tuple[str, Restaurant]):
        area_name = data[-1].area.replace(" ", "-")
        lclt_name = data[-1].locality.replace(" ", "-")
        city_name = data[-1].city.replace(" ", "-")
        city_id = data[0]
        clean_data = {
            "ids": f"locality_{lclt_name}__area_{area_name}__city_{city_name}-{city_id}",
            "name": data[-1].locality,
        }
        return clean_data


class Cuisine(BaseModel):
    name: str


class MainCuisine:
    main_cuisines: List[Cuisine]

    @classmethod  # create these cuisines manually later from Wikipedia
    def from_data(cls, data: Restaurant):
        return [{"name": cuis} for cuis in data.cuisines]


class SubCuisine:
    sub_cuisines: List[Cuisine]

    @model_validator(mode="before")
    @classmethod  # This is placeholder func
    def extract_and_transform(cls, data):
        return [Cuisine(name=_) for _ in data]


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
                    .get(item["address"]["country"], {})
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
                    .get(item["address"]["state"], "")
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
