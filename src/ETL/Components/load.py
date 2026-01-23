from queue import Queue
from itertools import chain
from falkordb import FalkorDB
from falkordb.graph import Graph
from concurrent.futures import ThreadPoolExecutor, wait
from typing import Literal, List, Any, Dict, Optional, Tuple
from time import time


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
    create_links,
)
from src.Utils.main_utils import read_json, fetch_batches, format_time

from src.Logging.logger import log_etl
from src.Exception.exception import LogException, CustomException


class GraphPool:
    """Quick method to create Graph instances for concurrent purposes."""

    def __init__(self, size: int = 4):
        self._pool = Queue(maxsize=size)

        for _ in range(size):
            self._pool.put(GraphPool.get_graph())

    def acquire(self) -> Graph:
        """
        Blocks until a Graph is available.
        Safe for ThreadPoolExecutor workers.
        """
        return self._pool.get(block=True)

    def release(self, graph: Graph) -> None:
        """
        Returns a Graph to the pool.
        MUST be called in finally block.
        """
        self._pool.put(graph)

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
        #  split params into admin_user and code_user
        fdb = FalkorDB()  # (**self.cyp_config.auth_params)
        return fdb.select_graph(graph_name)


class Loader:
    def __init__(self, cyp_config: ETLCypherConfig = ETLCypherConfig()):
        self.cyp_config = cyp_config

    def run(self):
        try:
            log_etl.info("Load: Communicating with FalkorDB")
            graph = GraphPool.get_graph()

            result = graph.query("MATCH (st: State) RETURN count(st) AS count")
            is_empty = result.result_set[0][0] == 0

            if is_empty:
                log_etl.info("Load: Starting initial Knowledge Graph setup")
                graph = self.create(graph)

            else:
                log_etl.info(
                    "Load: Knowledge Graph exists. Moving to upsert operations"
                )

            self.upsert(graph)

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

            log_etl.info("Load: Creating initial links")
            graph = create_links(graph, rlsp_data)

        except Exception as e:
            LogException(e, logger=log_etl)
            # raise CustomException(e)

        return graph

    def upsert(self, graph: Graph):
        try:
            instances = ETLCyphersConstants.NUMBER_OF_MT_WORKERS
            log_etl.info(f"Load: Preparing a KG pool of {instances}")
            self.graph_pool = GraphPool(instances)

            log_etl.info("Load: Starting batch upsertion with multi-threading")
            strt_time_main = time()
            with ThreadPoolExecutor(max_workers=instances) as pool:
                for batch in fetch_batches(batch_size=1024):
                    log_etl.info(
                        "Load: Preparing batch data for node and link creation"
                    )
                    strt_time_btch = time()
                    prepared = []
                    for i in range(instances):
                        slc = Loader.slice_batch(batch, i, instances)
                        node_data, rlsp_data = self._get_data("upsert", slc)
                        prepared.append((node_data, rlsp_data))

                    log_etl.info("Load: Started node creation for batch")
                    node_futures = []

                    for node_data, _ in prepared:
                        graph = self.graph_pool.acquire()
                        node_futures.append(
                            pool.submit(self._create_node_worker, graph, node_data)
                        )

                    wait(node_futures)  # HARD BARRIER

                    log_etl.info("Load: Started link creation for batch")
                    rlsp_futures = []

                    for _, rlsp_data in prepared:
                        graph = self.graph_pool.acquire()
                        rlsp_futures.append(
                            pool.submit(self._create_link_worker, graph, rlsp_data)
                        )

                    wait(rlsp_futures)  # HARD BARRIER

                    log_etl.info(
                        f"Load: Completed batch in {format_time(time() - strt_time_btch)}"
                    )

            log_etl.info(
                f"Load: Completed full upsertion in {format_time(time() - strt_time_main)}!"
            )

        except Exception as e:
            LogException(e, logger=log_etl)
            # raise CustomException(e)

    @staticmethod
    def slice_batch(
        batch: List[Dict[str, Any]],
        w_id: int,
        num_w: int,
    ) -> List[Dict[str, Any]]:
        """Static method that performs Round-Robin slicing on data.

        Args:
            batch (List[Dict[str, Any]]): Scraped Json data obtained in async batch format.
            w_id (int): Unique id for multi-threading worker.
            num_w (int): Total number of multi-threading workers.

        Returns:
            sliced_batch (List[Dict[str, Any]]): Non-overlapping sliced batch data for multi-thread processing.
        """
        return batch[w_id::num_w]

    def _create_node_worker(
        self,
        graph: Graph,
        node_data: Dict[NodeLabels, List[Any]],
    ):
        """Method to run node creation for each worker with sliced data.

        Args:
            graph (Graph): Graph instance to update
            node_data (Dict[NodeLabels, List[Any]]): Sliced data for node creation.
        """
        try:
            create_nodes(graph, node_data)
        finally:
            self.graph_pool.release(graph)

    def _create_link_worker(
        self,
        graph: Graph,
        rlsp_data: Dict[RelationshipLabels, List[Any]],
    ):
        """Method to run link creation for each worker with sliced data.

        Args:
            graph (Graph): Graph instance to update
            node_data (Dict[RelationshipLabels, List[Any]]): Sliced data for link creation.
        """
        try:
            create_links(graph, rlsp_data)
        finally:
            self.graph_pool.release(graph)

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
                    for data in read_json(path).values():
                        node_data[NodeLabels(key)].append(data)

                log_etl.info("Load: Appending relationship data")
                srch_data = {
                    "country_lookup": {
                        item["name"]: {"ids": item["ids"]}
                        for item in node_data[NodeLabels.COUNTRY]
                    },
                    "state_lookup": {
                        item["name"]: {"ids": item["ids"]}
                        for item in node_data[NodeLabels.STATE]
                    },
                }

                # MERGE (:Country {ids: ''})-[:HAS_STATE]->(:State {ids: ''})
                stte_dict_rlsp = [
                    RelationshipParams.from_data(
                        srch_data, RelationshipLabels.HAS_STATE, item
                    )
                    for item in node_data[NodeLabels.STATE]
                ]
                rlsp_data[RelationshipLabels.HAS_STATE] = stte_dict_rlsp

                # MERGE (:State {ids: ''})-[:HAS_CITY]->(:City {ids: ''})
                city_dict_rlsp = [
                    RelationshipParams.from_data(
                        srch_data, RelationshipLabels.HAS_CITY, item
                    )
                    for item in node_data[NodeLabels.CITY]
                ]
                rlsp_data[RelationshipLabels.HAS_CITY] = city_dict_rlsp

                del srch_data
                for item in chain.from_iterable(
                    chain(rlsp_data.values(), node_data.values())
                ):
                    # the '-' in 'ISO3166-2-lvl4' is causing Cypher to fail
                    # also, UNWIND is failing for nested data
                    item.pop("address", None)

            elif purpose == "upsert":
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
                city_data = read_json(city_path)
                city_keys = {key: val["ids"] for key, val in city_data.items()}
                del city_data  # clear memory

                for json_data in data_list:
                    try:
                        rstn = Restaurant(**json_data["data"])
                        menu = Menu(**json_data["data"])
                        key = rstn.city_id  # <- cleaned string
                        city_id = city_keys.get(key, "")
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
                            rl_data, RelationshipLabels.HAS_AREA
                        )
                        lclt_dict_rlsp = RelationshipParams.from_data(
                            rl_data, RelationshipLabels.HAS_LOCALITY
                        )
                        rstn_dict_rlsp = RelationshipParams.from_data(
                            rl_data, RelationshipLabels.HAS_RESTAURANT
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
                        # data that fails, upsert it to a different collection in MDB
                        # use same {"rstn_id": rstn.ids, 'config': json_data} format
                        # or create a new parameter 'processed':bool and select based on that
                        log_etl.info(f"{rstn.ids = }")
                        continue

                del data_list  # clear memory

            else:
                log_etl.info("Load: This is not supposed to happen!")
                pass

        except Exception as e:
            LogException(e, logger=log_etl)
            # raise CustomException(e)

        return node_data, rlsp_data
