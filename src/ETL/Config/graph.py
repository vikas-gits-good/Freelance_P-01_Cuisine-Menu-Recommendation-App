from pydantic import BaseModel
from typing import Literal


class BaseLocation(BaseModel):
    """Base model with common attributes for all location nodes.

    Args:
        ids (str): OpenStreetMap location identification format.
            `Ex: "osm_type:osm_id"`
        name (str): Location name in human readable form.
            `Example: "India", "Assam", 'Davangere'`
        coords (str): Latitude, Longitude with `,` delimiter.
            `Ex: "19.5670323,76.4164557"`
        boundingbox (str): Location enclosing latitude, longitude with `,` delimiter.
            `Ex: "15.6063596,22.0302694,72.6526112,80.8977842"`
    """

    ids: str
    name: str
    coords: str
    boundingbox: str


class Country(BaseLocation):
    """Model for `Country` node that extends `BaseLocation` **with** `iso_code`.

    Args:
        ids (str): OpenStreetMap location identification format.
            `Ex: "osm_type:osm_id"`
        name (str): Location name in human readable form.
            `Example: "India"`
        iso_code (str): ISO Code for the location.
            `Ex: "IN"`
        coords (str): Latitude, Longitude with `,` delimiter.
            `Ex: "19.5670323,76.4164557"`
        boundingbox (str): Location enclosing latitude, longitude with `,` delimiter.
            `Ex: "15.6063596,22.0302694,72.6526112,80.8977842"`
    """

    iso_code: str


class State(BaseLocation):
    """Model for `State` node that extends `BaseLocation` **with** `iso_code`.

    Args:
        ids (str): OpenStreetMap location identification format.
            `Ex: "osm_type:osm_id"`
        name (str): Location name in human readable form.
            `Example: "Assam"`
        iso_code (str): ISO Code for the location.
            `Ex: "IN-AS"`
        coords (str): Latitude, Longitude with `,` delimiter.
            `Ex: "19.5670323,76.4164557"`
        boundingbox (str): Location enclosing latitude, longitude with `,` delimiter.
            `Ex: "15.6063596,22.0302694,72.6526112,80.8977842"`
    """

    iso_code: str


class City(BaseLocation):
    """Model for `State` node that extends `BaseLocation` **without** `iso_code`.

    Args:
        ids (str): OpenStreetMap location identification format.
            `Ex: "osm_type:osm_id"`
        name (str): Location name in human readable form.
            `Example: "Assam"`
        coords (str): Latitude, Longitude with `,` delimiter.
            `Ex: "19.5670323,76.4164557"`
        boundingbox (str): Location enclosing latitude, longitude with `,` delimiter.
            `Ex: "15.6063596,22.0302694,72.6526112,80.8977842"`
    """

    pass


class RelationshipParams(BaseModel):
    """Model for relationship parameters that combines labels with node names.

    Args:
        label1 (str): Source node label.
            `Ex: Literal["Country", "State", "City", "Area", "Locality", "Restaurant", "Sub_Cuisine", "Main_Cuisine", "Menu_Item"]`
        label2 (str): Target node label.
            `Ex: Literal["Country", "State", "City", "Area", "Locality", "Restaurant", "Sub_Cuisine", "Main_Cuisine", "Menu_Item"]`
        relationship (str): Relationship name.
            `Ex: Literal["HAS_STATE", "HAS_CITY", "HAS_AREA", "HAS_LOCALITY", "HAS_RESTAURANT", "SERVES_SUB_CUISINE", "SERVES_MAIN_CUISINE", "HAS_MENU_ITEM"]`
        source_name (str): Source node name.
            `Ex: "India"`
        target_name (str): Target node name.
            `Ex: "Assam"`
    """

    label1: Literal[
        "Country",
        "State",
        "City",
        "Area",
        "Locality",
        "Restaurant",
        "Sub_Cuisine",
        "Main_Cuisine",
        "Menu_Item",
    ]
    label2: Literal[
        "Country",
        "State",
        "City",
        "Area",
        "Locality",
        "Restaurant",
        "Sub_Cuisine",
        "Main_Cuisine",
        "Menu_Item",
    ]
    relationship: Literal[
        "HAS_STATE",
        "HAS_CITY",
        "HAS_AREA",
        "HAS_LOCALITY",
        "HAS_RESTAURANT",
        "SERVES_SUB_CUISINE",
        "SERVES_MAIN_CUISINE",
        "HAS_MENU_ITEM",
    ]
    source_name: str
    target_name: str


class DataExtractionConfig(BaseModel):
    """Model for configuring how to extract data from source dictionary

    Args:
        source_key (str): Key to get source node name from data.
        target_key (str): Key to get target node name from data
        address_key (str): Nested dict key if source is in address
        default_source (str): Default source name if not found in data
    """

    source_key: str
    target_key: str
    address_key: str | None = None
    default_source: str | None = None
