import os
from concurrent.futures import ThreadPoolExecutor, wait
from time import time
from typing import Any, Dict, List, Literal

from falkordb.graph import Graph

from Src.Config import ETLCypherConfig, GraphPool
from Src.Constants import (
    ETLCyphersConstants,
    NodeLabels,
    RelationshipLabels,
)
from Src.Loader import (
    create_indexes,
    create_links,
    create_nodes,
)
from Src.Utils import LogException, fetch_batches, log_etl, util_func

from .transformer import Transformer


class ETL_Loader:
    def __init__(
        self,
        purpose: Literal["prod", "devl", "test"] = "prod",
        cyp_config: ETLCypherConfig = ETLCypherConfig(),
    ):
        self.purpose = purpose
        self.cyp_config = cyp_config
        self.transformer = Transformer()

    def run(self):
        try:
            log_etl.info("Loader: Communicating with FalkorDB")
            graph = GraphPool.get_graph(self.purpose)  # type: ignore

            result = graph.query("MATCH (st: State) RETURN count(st)")
            is_empty = result.result_set[0][0] == 0

            if is_empty:
                log_etl.info("Loader: Starting initial Knowledge Graph setup")
                graph = self.create(graph)

            else:
                log_etl.info(
                    "Loader: Knowledge Graph exists. Moving to upsert operations"
                )

            self.upsert(graph)

        except Exception as e:
            LogException(e, logger=log_etl)

    def create(self, graph: Graph) -> Graph:
        try:
            log_etl.info("Loader: Creating indexes on nodes")
            graph = create_indexes(graph)

            log_etl.info("Loader: Acquiring data for graph")
            node_data, rlsp_data = self.transformer.get_data(purpose="create")

            log_etl.info("Loader: Creating initial nodes")
            graph = create_nodes(graph, node_data)

            log_etl.info("Loader: Creating initial links")
            graph = create_links(graph, rlsp_data)

        except Exception as e:
            LogException(e, logger=log_etl)

        return graph

    def upsert(self, graph: Graph):
        try:
            instances = (
                int(os.getenv("LOADER_THREADS", "2"))
                if os.getenv("LOADER_THREADS")
                else ETLCyphersConstants.NUMBER_OF_MT_WORKERS
            )
            log_etl.info(f"Loader: Preparing a KG pool of {instances}")
            self.graph_pool = GraphPool(instances, self.purpose)  # type: ignore

            log_etl.info("Loader: Starting batch upsertion with multi-threading")
            strt_time_main = time()
            size = int(os.getenv("LOADER_BATCH_SIZE", "1024"))
            with ThreadPoolExecutor(max_workers=instances) as pool:
                for batch in fetch_batches(batch_size=size):
                    log_etl.info("Loader: Transforming batch data")
                    strt_time_btch = time()
                    prepared = []
                    for i in range(instances):
                        slc = ETL_Loader.slice_batch(batch, i, instances)
                        node_data, rlsp_data = self.transformer.get_data("upsert", slc)
                        prepared.append((node_data, rlsp_data))

                    del batch

                    log_etl.info("Loader: Started node creation for batch")
                    node_futures = []

                    for node_data, _ in prepared:
                        graph = self.graph_pool.acquire()
                        node_futures.append(
                            pool.submit(self._create_node_worker, graph, node_data)
                        )

                    wait(node_futures)  # HARD BARRIER

                    log_etl.info("Loader: Started link creation for batch")
                    rlsp_futures = []

                    for _, rlsp_data in prepared:
                        graph = self.graph_pool.acquire()
                        rlsp_futures.append(
                            pool.submit(self._create_link_worker, graph, rlsp_data)
                        )

                    wait(rlsp_futures)  # HARD BARRIER
                    del prepared

                    log_etl.info(
                        f"Loader: Completed batch in {util_func.format_time(time() - strt_time_btch)}"
                    )

            log_etl.info(
                f"Loader: Completed full upsertion in {util_func.format_time(time() - strt_time_main)}!"
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
