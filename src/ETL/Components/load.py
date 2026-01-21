from falkordb import FalkorDB
from falkordb.graph import Graph
from typing import Literal, List, Any, Dict, Optional, Union, Tuple

from asyncio import Queue

from src.ETL.Config import Restaurant, Menu
from src.ETL.Config.cyphers import ETLCypherConfig
from src.ETL.Config.models import Area, Locality, MainCuisine, RelationshipParams
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


class GraphPool:
    """Quick method to create Graph instances for sync/async/concurrent purposes."""

    def __init__(self, size: int = 4):
        """
        Initialising this class will append `size` number of `falkordb.graph.Graph` instances
        for async/concurrent use to an `asyncio.Queue`.

        Args:
            size (int): Number of graph instances, one per worker. Defaults to 4.
        """
        self.pool = Queue()
        _ = [self.pool.put(GraphPool.get_graph()) for _ in range(size)]

    def get(self):
        """
        Method to left-pop a `Graph` instance from `asyncio.Queue` for worker's use.

        Returns:
            graph (Graph): Graph object for async/concurrent use.
        """
        return self.pool.get()

    @staticmethod
    def get_graph(graph_name: Optional[str] = None) -> Graph:
        """
        Static Method that returns a single `Graph` instance.

        Returns:
            graph (Graph): Single `Graph` object
        """
        graph_name = (
            ETLCyphersConstants.KNOWLEDGE_GRAPH_NAME if not graph_name else graph_name
        )
        fdb = FalkorDB()  # (**self.cyp_config.auth_params)
        return fdb.select_graph(graph_name)


class Loader:
    def __init__(self, cyp_config: ETLCypherConfig = ETLCypherConfig()):
        self.cyp_config = cyp_config

    def run(self):
        try:
            log_etl.info("Load: Communicating with FalkorDB")
            #  split params into admin_user and code_user
            graph = GraphPool.get_graph()

            result = graph.query("MATCH (st: State) RETURN count(st) AS count")
            is_empty = result.result_set[0][0] == 0  # 33 for is_empty = False

            if is_empty:
                log_etl.info("Load: Starting initial Knowledge Graph setup")
                graph = self.create(graph)

            else:
                log_etl.info(
                    "Load: Knowledge Graph exists. Moving to upsert operations"
                )

            # graph = self.upsert(graph)

        except Exception as e:
            LogException(e, logger=log_etl)
            # raise CustomException(e)

    def create(self, graph: Graph) -> Graph:
        try:
            log_etl.info("Load: Creating indexes on nodes")
            graph = create_indexes(graph)

            log_etl.info("Load: Acquiring data for graph")
            node_data, rlsp_data = self._get_data(purpose="create")

            log_etl.info("Load: Creating initial nodes")
            graph = create_nodes(graph, node_data)

            log_etl.info("Load: Creating initial relationships")
            graph = create_relationships(graph, rlsp_data)

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

    def _get_data(
        self,
        purpose: Literal["create", "upsert"] = "create",
        data_list: List[Dict[str, Any]] = [{}],
    ) -> Tuple[Dict[NodeLabels, List[Any]], Dict[RelationshipLabels, List[Any]]]:
        node_data = {}
        rlsp_data = {}
        try:
            if purpose == "create":
                log_etl.info("Load: Appending node data")
                node_data = {
                    NodeLabels.COUNTRY: [],
                    NodeLabels.STATE: [],
                    NodeLabels.CITY: [],
                }
                path_list = LocationConstants.LOCATION_DATA_FILE_PATHS
                for path in path_list:
                    # "unq_ids_city.json" -> "City"
                    key = path.split("/")[-1][:-5].split("_")[-1].capitalize()
                    node_data[NodeLabels(key)].append(read_json(path))

                log_etl.info("Load: Appending relationship data")
                country_lookup = {
                    item["name"]: {"ids": item["ids"]}
                    for item in node_data[NodeLabels.COUNTRY]
                }
                state_lookup = {
                    item["name"]: {"ids": item["ids"]}
                    for item in node_data[NodeLabels.STATE]
                }

                # MERGE (:Country {ids: ''})-[:HAS_STATE]->(:State {ids: ''})
                rlsp_data[RelationshipLabels.HAS_STATE] = [
                    {
                        "source": country_lookup.get(item["address"]["country"], {}),
                        "target": {"ids": item["ids"]},
                        "params": {},
                    }
                    for item in node_data[NodeLabels.STATE]
                ]
                del country_lookup

                # MERGE (:State {ids: ''})-[:HAS_CITY]->(:City {ids: ''})
                rlsp_data[RelationshipLabels.HAS_CITY] = [
                    {
                        "source": state_lookup.get(item["address"]["state"], {}),
                        "target": {"ids": item["ids"]},
                        "params": {},
                    }
                    for item in node_data[NodeLabels.CITY]
                ]
                del state_lookup

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
                rlsp_data = {
                    RelationshipLabels.HAS_AREA: [],
                    RelationshipLabels.HAS_LOCALITY: [],
                    RelationshipLabels.HAS_RESTAURANT: [],
                    RelationshipLabels.HAS_MENU: [],
                    RelationshipLabels.SERVES_MAIN_CUISINE: [],
                    # RelationshipLabels.SERVES_SUB_CUISINE: [],
                    # include in production
                }

                city_path = "src/ETL/Data/unq_ids_city.json"
                city_data = read_json(city_path)  #
                city_keys = {key: val["ids"] for key, val in city_data.items()}
                del city_data  # clear memory

                for json_data in data_list:
                    try:
                        rstn = Restaurant(**json_data["data"])
                        menu = Menu(**json_data["data"])
                        key = rstn.city.lower()  # Bangalore, Bengaluru
                        # You need to update the keys of the dict. replace '_','-' with ' '
                        # using rstn.city_id with the city id from url with '-'
                        city_id = city_keys.get(key, "").get("ids", "")
                        # see if you can generate uuid for city_id incase of failure

                        area_dict_node = Area.from_data((city_id, rstn))
                        lclt_dict_node = Locality.from_data((city_id, rstn))
                        rstn_dict_node = rstn.model_dump()
                        menu_dict_node = menu.model_dump()["food_items"]
                        mcui_dict_node = MainCuisine.from_data(rstn)
                        # scui_dict_node = SubCuisine.from_data(rstn)

                        node_data[NodeLabels.AREA].append(area_dict_node)
                        node_data[NodeLabels.LOCALITY].append(lclt_dict_node)
                        node_data[NodeLabels.RESTAURANT].append(rstn_dict_node)
                        node_data[NodeLabels.MENU].append(menu_dict_node)
                        node_data[NodeLabels.MAINCUISINE].append(mcui_dict_node)
                        # node_data[NodeLabels.SUBCUISINE].append(scui_dict_node)

                        rl_data = {
                            "city_id": city_id,
                            "rstn": rstn,
                            "menu": menu,
                            "area_dict_node": area_dict_node,
                            "lclt_dict_node": lclt_dict_node,
                        }

                        area_dict_rlsp = RelationshipParams.from_data(
                            rl_data, types=RelationshipLabels.HAS_AREA
                        )
                        lclt_dict_rlsp = RelationshipParams.from_data(
                            rl_data, types=RelationshipLabels.HAS_LOCALITY
                        )
                        rstn_dict_rlsp = RelationshipParams.from_data(
                            rl_data, types=RelationshipLabels.HAS_RESTAURANT
                        )
                        menu_dict_rlsp = [
                            RelationshipParams.from_data(
                                rl_data, RelationshipLabels.HAS_MENU, food
                            )
                            for food in menu.food_items
                        ]
                        mcui_dict_rlsp = [
                            RelationshipParams.from_data(
                                rl_data, RelationshipLabels.SERVES_MAIN_CUISINE, cuisine
                            )
                            for cuisine in rstn.cuisines
                        ]
                        # mcui_dict_rlsp = [
                        #     RelationshipParams.from_data(
                        #         rl_data, RelationshipLabels.SERVES_SUB_CUISINE, cuisine
                        #     )
                        #     for cuisine in rstn.cuisines
                        # ]

                        # MERGE (:City {ids: ''})-[:HAS_AREA]->(:Area {ids: ''})
                        rlsp_data[RelationshipLabels.HAS_AREA].append(area_dict_rlsp)

                        # MERGE (:Area {ids: ''})-[:HAS_LOCALITY]->(:Locality {ids: ''})
                        rlsp_data[RelationshipLabels.HAS_LOCALITY].append(
                            lclt_dict_rlsp
                        )

                        # MERGE (:Locality {ids: ''})-[:HAS_RESTAURANT]->(:Restaurant {ids: ''})
                        rlsp_data[RelationshipLabels.HAS_RESTAURANT].append(
                            rstn_dict_rlsp
                        )

                        # MERGE (:Restaurant {ids: ''})-[:HAS_MENU]->(:Menu {name: ''})
                        rlsp_data[RelationshipLabels.HAS_MENU].append(menu_dict_rlsp)

                        # MERGE (:Restaurant {ids: ''})-[:SERVES_MAIN_CUISINE]->(:Cuisine {name: ''})
                        rlsp_data[RelationshipLabels.SERVES_MAIN_CUISINE].append(
                            mcui_dict_rlsp
                        )

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

        return node_data, rlsp_data
