from falkordb import FalkorDB
from falkordb.graph import Graph
from typing import Literal, List, Any, Dict, Optional, Union

from src.ETL.Config import Restaurant, Menu
from src.ETL.Config.cyphers import ETLCypherConfig
from src.ETL.Config.models import (
    Country,
    State,
    City,
    Area,
    Locality,
    MainCuisine,
    RelationshipParams,
    DataExtractionConfig,
)
from src.ETL.Constants.cyphers import (
    ETLCyphersConstants,
    NodeLabels,
    RelationshipLabels,
    LocationConstants,
)
from src.ETL.Utils.graph import (
    create_indexes,
    create_nodes,
    create_relationships,
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
            graph = create_indexes(graph)

            log_etl.info("Load: Preparing data for nodes")
            node_data = self._get_node_data(purpose="create")

            log_etl.info("Load: Creating initial nodes")
            graph = create_nodes(graph, node_data)

            log_etl.info("Load: Preparing data for relationships")
            node_data = self._get_relationship_data(purpose="create")

            log_etl.info("Load: Creating initial relationships")
            graph = create_relationships(graph, node_data)

            log_etl.info("Load: Creating relationships b/w Country and State")
            # MERGE (:Country)-[:HAS_STATE]->(:State)
            rp = RelationshipParams(
                source_label=NodeLabels.COUNTRY.value,
                relationship=RelationshipLabels.HAS_STATE.value,
                target_label=NodeLabels.STATE.value,
            )
            dec = DataExtractionConfig(
                source_key="country",
                target_key="name",
                address_key="address",
                default_source="India",
            )
            graph = create_relationships(
                graph=graph,
                labels=rp,
                extraction_config=dec,
                data_dict=data_list[1],  # state
            )

            log_etl.info("Load: Creating relationships b/w State and City")
            # MERGE (:State)-[:HAS_CITY]->(:City)
            rp = RelationshipParams(
                source_label=NodeLabels.STATE.value,
                relationship=RelationshipLabels.HAS_CITY.value,
                target_label=NodeLabels.CITY.value,
            )
            dec = DataExtractionConfig(
                source_key="state",
                target_key="name",
                address_key="address",
            )
            graph = create_relationships(
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
            log_etl.info("Load: Creating nodes in parallel")

            json_data_list: list[dict] = [{}]
            area_dict, rstn_dict, menu_dict, mcui_dict, scui_dict = {}, {}, {}, {}, {}

            for i, json_data in enumerate(json_data_list):
                rstn = Restaurant(**json_data["data"])
                menu = Menu(**json_data["data"])  # list[FoodItem]

                area_dict.update({i: {"city_id": "", "rstn": rstn}})
                rstn_dict.update({i: {"rstn": rstn}})
                menu_dict.update({i: {"menu": menu}})
                mcui_dict.update({i: {"rstn": rstn}})
                # scui_dict.update({i: {"rstn": rstn}})

            # area and locality share same data_dict
            model_list = [
                Area,
                Locality,
                Restaurant,
                Menu,
                MainCuisine,
                # SubCuisine,
            ]
            data_list = [
                area_dict,
                area_dict,
                rstn_dict,
                menu_dict,
                mcui_dict,
                # scui_dict,
            ]

            for model, data in zip(model_list, data_list):
                graph = create_nodes(graph, model, data)

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

    def _get_node_data(
        self,
        purpose: Literal["create", "upsert"] = "create",
        data_list: List[Dict[str, Any]] = [{}],
    ) -> Dict[NodeLabels, List[Any]]:
        # see if you can add another variable that can keep relationship data
        node_data = {}
        try:
            log_etl.info("Load: Appending node data")
            if purpose == "create":
                node_data = {
                    NodeLabels.COUNTRY: [],
                    NodeLabels.STATE: [],
                    NodeLabels.CITY: [],
                }
                path_list = LocationConstants.LOCATION_DATA_FILE_PATHS
                for path in path_list:
                    # "unq_ids_city.json" -> "City"
                    key = path.split("/")[-1][:-5].split("_")[-1].capitalize()
                    node_data[key].append(read_json(path))

            elif purpose == "upsert":
                log_etl.info("Load: Extracting from scraped json data")
                node_data = {
                    NodeLabels.AREA: [],
                    NodeLabels.LOCALITY: [],
                    NodeLabels.RESTAURANT: [],
                    NodeLabels.MENU: [],
                    NodeLabels.MAINCUISINE: [],
                    # NodeLabels.SUBCUISINE: [],  # include in production
                }

                city_path = "src/ETL/Data/unq_ids_city.json"
                city_data = read_json(city_path)
                city_keys = {key: val["ids"] for key, val in city_data.items()}
                del city_data  # clear memory

                for json_data in data_list:
                    try:
                        rstn = Restaurant(**json_data["data"])
                        menu = Menu(**json_data["data"])
                        key = rstn.city.lower()
                        city_id = city_keys.get(key, "").get("ids", "")
                        # see if you can generate uuid for city_id incase of failure

                        node_data[NodeLabels.AREA].append(
                            Area.from_data((city_id, rstn))
                        )
                        node_data[NodeLabels.LOCALITY].append(
                            Locality.from_data((city_id, rstn))
                        )
                        node_data[NodeLabels.RESTAURANT].append(rstn.model_dump())
                        node_data[NodeLabels.MENU].append(
                            menu.model_dump()["food_items"]
                        )
                        node_data[NodeLabels.MAINCUISINE].append(
                            MainCuisine.from_data(rstn)
                        )
                        # node_data[NodeLabels.SUBCUISINE].append(SubCuisine())

                    except Exception as e:
                        LogException(e, logger=log_etl)
                        continue

                del data_list  # clear memory

            else:
                log_etl.info("Load: This is not supposed to happen!")
                pass

        except Exception as e:
            LogException(e, logger=log_etl)
            # raise CustomException(e)

        return node_data
