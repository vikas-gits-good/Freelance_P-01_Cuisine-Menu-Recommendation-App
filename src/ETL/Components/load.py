from pathlib import Path
from falkordb import FalkorDB
from falkordb.graph import Graph

from src.ETL.Config.cyphers import ETLCypherConfig
from src.ETL.Config.models import (
    Country,
    State,
    City,
    RelationshipParams,
    DataExtractionConfig,
)
from src.ETL.Constants.cyphers import (
    ETLCyphersConstants,
    NodeLabels,
    RelationshipTypes,
    LocationConstants,
)
from src.ETL.Utils.graph import (
    create_indexes,
    create_location_nodes,
    create_location_relationships,
)
from src.Utils.main_utils import read_json

from src.Logging.logger import log_etl
from src.Exception.exception import LogException, CustomException


class Loader:
    def __init__(self, cyp_config: ETLCypherConfig = ETLCypherConfig()):
        self.cyp_config = cyp_config

    def run(self):
        try:
            log_etl.info("Load: Communicating with FalkorDB")
            #  split params into admin_user and code_user
            fdb = FalkorDB()  # (**self.cyp_config.auth_params)
            graph = fdb.select_graph(ETLCyphersConstants.KNOWLEDGE_GRAPH_NAME)

            result = graph.query("MATCH (n) RETURN count(n) AS count")
            is_empty = result.result_set[0][0] == 0

            if is_empty:
                log_etl.info("Load: Starting initial Knowledge Graph setup")
                graph = self.tapa(graph)

            else:
                log_etl.info(
                    "Load: Knowledge Graph exists. Moving to upsert operations"
                )

            graph = self.upsert(graph)

        except Exception as e:
            LogException(e, logger=log_etl)
            # raise CustomException(e)

    def tapa(self, graph: Graph) -> Graph:
        try:
            log_etl.info("Load: Creating indexes on nodes")
            for node in [NodeLabels.COUNTRY, NodeLabels.STATE, NodeLabels.CITY]:
                graph = create_indexes(graph, node.value)

            log_etl.info("Load: Creating initial nodes for Country, State, City")
            model_list = [Country, State, City]  # Dont add Area and Locality here
            data_list = self._get_loc_data()
            for model, data in zip(model_list, data_list):
                graph = create_location_nodes(graph, model, data)

            log_etl.info("Load: Creating relationships b/w Country and State")
            # MERGE (:Country)-[:HAS_STATE]->(:State)
            rp = RelationshipParams(
                source_label=NodeLabels.COUNTRY.value,
                relationship=RelationshipTypes.HAS_STATE.value,
                target_label=NodeLabels.STATE.value,
            )
            dec = DataExtractionConfig(
                source_key="country",
                target_key="name",
                address_key="address",
                default_source="India",
            )
            graph = create_location_relationships(
                graph=graph,
                labels=rp,
                extraction_config=dec,
                data_dict=data_list[1],  # state
            )

            log_etl.info("Load: Creating relationships b/w State and City")
            # MERGE (:State)-[:HAS_CITY]->(:City)
            rp = RelationshipParams(
                source_label=NodeLabels.STATE.value,
                relationship=RelationshipTypes.HAS_CITY.value,
                target_label=NodeLabels.CITY.value,
            )
            dec = DataExtractionConfig(
                source_key="state",
                target_key="name",
                address_key="address",
            )
            graph = create_location_relationships(
                graph=graph,
                labels=rp,
                extraction_config=dec,
                data_dict=data_list[2],  # city
            )

        except Exception as e:
            LogException(e, logger=log_etl)
            # raise CustomException(e)

        return graph

    def upsert(self, graph: Graph) -> Graph:
        try:
            # identify the attributes of the node types
            # Area, Locality, Restaurant, Menu | (Sub_cuisine) Main Cuisine
            # area, locality, restaurant, menu_item, main_cuisine (dont add subcuisine)
            # for the time being you'll also need to use sentence transformer to classify

            # figure out what falttened format will allow you to create all nodes
            # find a way to get json_data in batches of 1024 - 2048
            # run json_data in stream async/concurrent 4 workers fashion to flatten
            # the food item cuisine
            # create general template cyphers to upsert based on node attributes

            ...
            pass

        except Exception as e:
            LogException(e, logger=log_etl)
            # raise CustomException(e)

        return graph

    def _get_loc_data(self):
        data = []
        try:
            path_list = LocationConstants.LOCATION_DATA_FILE_PATHS
            # reorder list
            order = {
                "unq_ids_country.json": 0,
                "unq_ids_state.json": 1,  # use same order as model_list
                "unq_ids_city.json": 2,
            }
            path_list = sorted(
                path_list, key=lambda path: order.get(Path(path).name, 999)
            )
            data = [read_json(path) for path in path_list]

        except Exception as e:
            LogException(e, logger=log_etl)
            # raise CustomException(e)

        return data


"""
Area:
    ids: f"area_{rstn_area.replace(' ', '-')}__city_{city_name}-{relation:123456}"
    name: rstn_area

Locality:
    ids: f"locality_{rstn_locality.replace(' ', '-')}__area_{rstn_area.replace(' ', '-')}__city_{city_name}-{relation:123456}"
    name: rstn_locality

Restaurant: # change either graph attribute or BaseModel attribute names. No rstn_*, food_* prefixes
    rstn_id: int # dont conv dtype
    rstn_name: str
    rstn_city: str
    rstn_area: str
    rstn_locality: str
    rstn_cuisines: List[str] # main cuisine now, sub cuisine later.
    rstn_rating: float # dont conv dtype
    rstn_address: str
    rstn_coords: str
    rstn_chain: bool # dont conv dtype

Menu:
    food_name: str
    food_category: str # do i need this
    food_description: str # some data aren't descriptions. do i '' those?
    food_price: int # dont conv dtype
    food_rating: float # dont conv dtype
    food_type: Literal["VEG", "NONVEG", "EGG", "UNKNOWN"]
    food_cuisine: str


"""
