from falkordb.graph import Graph
from typing import Dict, Any
from src.ETL.Config import Restaurant, Menu
from src.ETL.Config.cyphers import ETLCypherConfig
from src.ETL.Config.models import (
    BaseLocation,
    RelationshipParams,
    DataExtractionConfig,
    Cuisine,
)
from src.ETL.Constants.cyphers import NodeLabels

from src.Logging.logger import log_etl
from src.Exception.exception import LogException, CustomException

ecc = ETLCypherConfig()


def create_indexes(graph: Graph, label: str) -> Graph:
    """Create indexes on node IDs and name for better query performance."""
    try:
        query = ecc.cp_code.create.get("create_index", "").format(label=label)
        # you need to split the query for index
        for q in query.split("\n"):
            graph.query(q)

    except Exception as e:
        LogException(e, logger=log_etl)

    return graph


def create_nodes(
    graph: Graph,
    model: type[BaseLocation] | type[Restaurant] | type[Menu] | type[Cuisine],
    data: Dict[Any, Any],
):
    """
    Generic function to create nodes for `Country, State, City, Area, Locality, Restaurant, Menu, MainCuisine, SubCuisine`.

    Args:
        graph (Graph): `falkordb.graph.Graph` object to create nodes on.
        model (type[BaseLocation] | type[Restaurant] | type[Menu] | type[Cuisine]): Pydantic model class.
        data (Dict[str, Any]): Dictionary containing data.


    Returns:
        graph (Graph): Updated `Graph` object.
    """

    try:
        label: str = model.__name__
        location_lables: list[str] = [member.value for member in NodeLabels][:5]
        location: bool = label in location_lables

        key, code = {
            **(
                {
                    label: [
                        "create_country_state_city_area_locality",
                        ecc.cp_code.create,
                    ]
                }
                if location
                else {}
            ),
            "Restaurant": [
                "create_restaurant",
                ecc.cp_code.upsert,
            ],
            "Menu": [
                "create_menu",
                ecc.cp_code.upsert,
            ],
            "Cuisine": [
                "create_cuisine",
                ecc.cp_code.upsert,
            ],
        }.get(label, ["", ""])

        query = code[key].format(label=label)

        for val in data.values():
            try:
                # For Country, State, City
                if label in location_lables[:3]:
                    location_obj = model(**val)

                # For Area, Locality
                elif label in location_lables[3:]:
                    location_obj = model((val["city_id"], val["rstn"]))

                # For Restaurant, Menu, Cuisine?
                elif label in ["Restaurant", "Menu"]:
                    location_obj = model(**val["data"])

                # For MainCuisine, SubCuisine
                else:
                    location_obj = model(val)

                params = location_obj.model_dump()
                graph.query(query, params)

            except Exception as e:
                LogException(e, logger=log_etl)
                continue

    except Exception as e:
        LogException(e, logger=log_etl)
        # raise CustomException(e)

    return graph


def create_link(graph: Graph, params: RelationshipParams) -> Graph:
    """
    Generic function to create relationships between nodes.

    Args:
        graph (Graph): `falkordb.graph.Graph` object to create nodes on.
        params (RelationshipParams): `RelationshipParams` object containing all relationship information

    Returns:
        graph (Graph): Updated `Graph` object.
    """
    try:
        query = ecc.cp_code.create.get("create_location_relationship", "").format(
            source_label=params.source_label,
            target_label=params.target_label,
            relationship=params.relationship,
        )
        query_params = {
            "source_name": params.source_name,
            "target_name": params.target_name,
        }
        graph.query(query, query_params)

    except Exception as e:
        LogException(e, logger=log_etl)
        # raise CustomException(e)

    return graph


def create_relationships(
    graph: Graph,
    labels: RelationshipParams,
    extraction_config: DataExtractionConfig,
    data_dict: dict,
):
    """
    Generic function to create relationships between nodes

    Args:
        graph (Graph): `falkordb.graph.Graph` object to create nodes on.
        labels: `RelationshipParams` object with labels and relationship.
        extraction_config: DataExtractionConfig object with keys and defaults for data extraction
        data_dict: Dictionary containing data for target nodes

    Returns:
        graph (Graph): Updated `Graph` object.
    """

    for data in data_dict.values():
        try:
            if extraction_config.address_key:
                source_name = data.get(extraction_config.address_key, {}).get(
                    extraction_config.source_key, extraction_config.default_source
                )
            else:
                source_name = data.get(
                    extraction_config.source_key, extraction_config.default_source
                )
            target_name = data.get(extraction_config.target_key)

            setattr(labels, "source_name", source_name)
            setattr(labels, "target_name", target_name)

            # Create the relationship
            graph = create_link(graph, labels)

        except Exception as e:
            LogException(e, logger=log_etl)
            continue

    return graph
