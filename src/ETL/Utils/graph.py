from falkordb.graph import Graph
from typing import Dict, Any, List
from src.ETL.Config.cyphers import ETLCypherConfig
from src.ETL.Config.models import RelationshipParams
from src.ETL.Constants.cyphers import NodeLabels, IndexName, RelationshipLabels

from src.Logging.logger import log_etl
from src.Exception.exception import LogException, CustomException

ecc = ETLCypherConfig()


def create_indexes(graph: Graph) -> Graph:
    """
    Create indexes on node IDs and name for better query performance.

    ## Format
    ```cypher
    CREATE INDEX {index_name} FOR (c:{index_label}) ON (c.{index_id})
    ```
    """
    label_lookup = {label.value.lower(): label.value for label in NodeLabels}
    for index_name in IndexName:
        try:
            parts = index_name.value.split("_")
            label_key = parts[0]  # "country", "subcuisine"
            id_type = parts[1]  # "ids", "name"

            query = ecc.cp_code.create.get("create_index", "").format(
                # index_name=index_name.value,
                index_label=label_lookup[label_key],
                index_id=id_type,
            )
            graph.query(query)

        except Exception as e:
            LogException(e, logger=log_etl)
            continue

    return graph


def create_nodes(
    graph: Graph,
    data: Dict[NodeLabels, List[Any]],
):
    """
    Generic function to create nodes for `Country, State, City, Area, Locality, Restaurant, Menu, MainCuisine, SubCuisine`.

    Args:
        graph (Graph): `falkordb.graph.Graph` object to create nodes on.
        data (Dict[NodeLabels, Any]): Dictionary containing data.


    Returns:
        graph (Graph): Updated `Graph` object.
    """
    for node_name, node_params in data.items():
        try:
            if node_name in [loc for loc in NodeLabels][:5]:
                query = ecc.cp_code.create["create_country_state_city_area_locality"]

            elif node_name == NodeLabels.RESTAURANT:
                query = ecc.cp_code.upsert["upsert_restaurant"]

            elif node_name == NodeLabels.MENU:
                query = ecc.cp_code.upsert["upsert_menu"]

            elif node_name == NodeLabels.MAINCUISINE:
                query = ecc.cp_code.upsert["upsert_cuisine"]

            # elif node_name == NodeLabels.SUBCUISINE:
            #     query = ecc.cp_code.upsert["upsert_cuisine"]

            else:
                query = ""

            query = query.format(label=node_name.value)
            graph.query(query, {"rows": node_params})

        except Exception as e:
            LogException(e, logger=log_etl)
            continue

    return graph


def create_links(
    graph: Graph,
    data_dict: Dict[RelationshipLabels, List[Any]],
):
    """
    Generic function to create relationships between nodes.

    Args:
        graph (Graph): `falkordb.graph.Graph` object to create relationships on.
        data_dict (Dict[RelationshipLabels, List[Any]]): Dictionary containing data for relationships.
        chunk_size (int): chunk large data into smaller sizes.

    Returns:
        graph (Graph): Updated `Graph` object.
    """
    rlsp_label_list = [rlsp for rlsp in RelationshipLabels]
    for rlsp_name, rlsp_params in data_dict.items():
        try:
            if rlsp_name in rlsp_label_list[:5]:
                query = ecc.cp_code.create["create_location_relationship"]

            elif rlsp_name in rlsp_label_list[5:]:
                query = ecc.cp_code.upsert["upsert_relationship_with_params"]

            else:
                query = ""

            # rlsp_params is a list[dict] or a list[list[dict]]
            first_item = (
                rlsp_params[0][0]
                if isinstance(rlsp_params[0], list)
                else rlsp_params[0]
            )
            query = query.format(
                source_label=first_item["source_label"],
                target_label=first_item["target_label"],
                relationship=first_item["relationship"],
            )

            graph.query(query, {"rows": rlsp_params})

        except Exception as e:
            LogException(e, logger=log_etl)
            continue

    return graph
