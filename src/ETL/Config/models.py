from typing import Optional
from pydantic import BaseModel


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

    Args:
        ids (str): Unique id derive from area and city.
            `Ex: "area_{name}__city_{osmtype}:{osmid}"`
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


class Locality(BaseLocation):
    """Model for `Locality` node.

    Args:
        ids (str): Unique id derive from locality, area and city.
            `Ex: "location_{name}__area_{name}__city_{osmtype}:{osmid}"`
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


class RelationshipParams(BaseModel):
    """Model for relationship parameters that combines labels with node names.

    Args:
        source_label (str): Source node label.
            `Ex: Literal["Country", "State", "City", "Area", "Locality", "Restaurant", "Sub_Cuisine", "Main_Cuisine", "Menu_Item"]`
        target_label (str): Target node label.
            `Ex: Literal["Country", "State", "City", "Area", "Locality", "Restaurant", "Sub_Cuisine", "Main_Cuisine", "Menu_Item"]`
        relationship (str): Relationship name.
            `Ex: Literal["HAS_STATE", "HAS_CITY", "HAS_AREA", "HAS_LOCALITY", "HAS_RESTAURANT", "SERVES_SUB_CUISINE", "SERVES_MAIN_CUISINE", "HAS_MENU_ITEM"]`
        source_name (Optional[str]): Source node name.
            `Ex: "India"`
        target_name (Optional[str]): Target node name.
            `Ex: "Assam"`
    """

    source_label: str
    target_label: str
    relationship: str
    source_name: Optional[str] = None
    target_name: Optional[str] = None


class DataExtractionConfig(BaseModel):
    """Model for configuring how to extract data from source dictionary

    Args:
        source_key (str): Key to get source node name from data.
        target_key (str): Key to get target node name from data
        address_key (Optional[str]): Nested dict key if source is in address
        default_source (Optional[str]): Default source name if not found in data
    """

    source_key: str
    target_key: str = "name"
    address_key: Optional[str] = None
    default_source: Optional[str] = None
