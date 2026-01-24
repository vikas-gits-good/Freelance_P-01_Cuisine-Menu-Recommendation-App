from time import time
from falkordb.graph import Graph
from typing import List, Any, Dict, Literal
from concurrent.futures import ThreadPoolExecutor, wait

from src.ETL.Components.transform import Transformer
from src.ETL.Config.cyphers import ETLCypherConfig
from src.ETL.Config.graph_pool import GraphPool
from src.ETL.Constants.cyphers import (
    ETLCyphersConstants,
    NodeLabels,
    RelationshipLabels,
)
from src.ETL.Utils.graph import (
    create_indexes,
    create_nodes,
    create_links,
)
from src.Utils.main_utils import fetch_batches, format_time

from src.Logging.logger import log_etl
from src.Exception.exception import LogException, CustomException


class Loader:
    def __init__(
        self,
        purpose: Literal["production", "development", "test"] = "production",
        cyp_config: ETLCypherConfig = ETLCypherConfig(),
    ):
        self.purpose = purpose
        self.cyp_config = cyp_config
        self.transformer = Transformer()

    def run(self):
        try:
            log_etl.info("Load: Communicating with FalkorDB")
            graph = GraphPool.get_graph(self.purpose)

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
            node_data, rlsp_data = self.transformer.get_data(purpose="create")

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
            self.graph_pool = GraphPool(instances, self.purpose)

            log_etl.info("Load: Starting batch upsertion with multi-threading")
            strt_time_main = time()
            with ThreadPoolExecutor(max_workers=instances) as pool:
                for batch in fetch_batches(batch_size=1024):
                    log_etl.info(
                        "Load: Transforming batch data for node and link creation"
                    )
                    strt_time_btch = time()
                    prepared = []
                    for i in range(instances):
                        slc = Loader.slice_batch(batch, i, instances)
                        node_data, rlsp_data = self.transformer.get_data("upsert", slc)
                        prepared.append((node_data, rlsp_data))

                    del batch

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
                    del prepared

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
            batch (List[Dict[str, Any]]): Scraped .json data obtained in batch format.
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
