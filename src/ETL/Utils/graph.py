from falkordb.graph import Graph

from src.ETL.Config.cyphers import ETLCypherConfig
from src.ETL.Config.models import BaseLocation, RelationshipParams, DataExtractionConfig

from src.Logging.logger import log_etl
from src.Exception.exception import LogException, CustomException

ecc = ETLCypherConfig()


def create_indexes(graph: Graph, label: str) -> Graph:
    """Create indexes on node IDs and name for better query performance."""
    try:
        query = ecc.cp_code.create.get("create_index", "").format(loc_label=label)
        # you need to split the query for index
        for q in query.split("\n"):
            graph.query(q)

    except Exception as e:
        LogException(e, logger=log_etl)

    return graph


def create_location_nodes(
    graph: Graph,
    location_model: type[BaseLocation],
    data_dict: dict,
):
    """
    Generic function to create location nodes (Country, State, or City)

    Args:
        graph (Graph): `Falkordb.graph.Graph` object to create nodes on.
        location_model: Pydantic model class (Country, State, City, Area, Locality).
        data_dict: Dictionary containing location data.

    Returns:
        graph (Graph): Updated `Graph` object.
    """
    location_label = location_model.__name__
    has_iso_code = "iso_code" in location_model.model_fields

    for data in data_dict.values():
        try:
            if has_iso_code:
                query = ecc.cp_code.create.get(
                    "create_location_with_iso_code", ""
                ).format(loc_label=location_label)
            else:
                query = ecc.cp_code.create.get(
                    "create_location_without_iso_code", ""
                ).format(loc_label=location_label)

            # Create Pydantic model instance and convert to dict
            if location_label == "Country":
                location_obj = location_model(
                    ids=data["ids"],
                    name=data["name"],
                    iso_code=data["iso_code"],
                    coords=data["coords"],
                    boundingbox=data["boundingbox"],
                )
            elif location_label == "State":
                location_obj = location_model(
                    ids=data["ids"],
                    name=data["name"],
                    iso_code=data["address"].get("ISO3166-2-lvl4", ""),
                    coords=data["coords"],
                    boundingbox=data["boundingbox"],
                )
            elif location_label == "City":
                location_obj = location_model(
                    ids=data["ids"],
                    name=data["name"],
                    coords=data["coords"],
                    boundingbox=data["boundingbox"],
                )
            elif location_label == "Area":
                location_obj = location_model(
                    ids=data["ids"],
                    name=data["name"],
                )
            elif location_label == "Locality":
                location_obj = location_model(
                    ids=data["ids"],
                    name=data["name"],
                )

            params = location_obj.model_dump()
            graph.query(query, params)

        except Exception as e:
            LogException(e, logger=log_etl)
            continue

    return graph


def create_relationship(graph: Graph, params: RelationshipParams) -> Graph:
    """
    Generic function to create relationships between nodes.

    Args:
        graph (Graph): `Falkordb.graph.Graph` object to create nodes on.
        params: RelationshipParams object containing all relationship information

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


def create_location_relationships(
    graph: Graph,
    labels: RelationshipParams,
    extraction_config: DataExtractionConfig,
    data_dict: dict,
):
    """
    Unified function to create relationships between location nodes

    Args:
        graph (Graph): `Falkordb.graph.Graph` object to create nodes on.
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
            graph = create_relationship(graph, labels)

        except Exception as e:
            LogException(e, logger=log_etl)
            continue

    return graph
