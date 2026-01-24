from queue import Queue
from typing import Literal
from falkordb import FalkorDB
from falkordb.graph import Graph

from src.ETL.Constants.cyphers import ETLCyphersConstants


class GraphPool:
    """Quick method to create Graph instances for concurrent purposes."""

    def __init__(
        self,
        size: int = 4,
        graph_name: Literal["production", "development", "test"] = "production",
    ):
        self._pool = Queue(maxsize=size)

        for _ in range(size):
            self._pool.put(GraphPool.get_graph(graph_name))

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
    def get_graph(
        graph_name: Literal["production", "development", "test"] = "production",
    ) -> Graph:
        """Static Method that returns a single `Graph` instance.

        Args:
            graph_name (Literal[&quot;production&quot;, &quot;development&quot;, &quot;test&quot;], optional): Name of the graph to return. Defaults to `"production"`.

        Returns:
            graph (Graph): Single `Graph` object.
        """
        ecc = ETLCyphersConstants
        name = {
            "production": ecc.KG_NAME_PROD,
            "development": ecc.KG_NAME_DEVL,
            "test": ecc.KG_NAME_TEST,
        }.get(graph_name, ecc.KG_NAME_PROD)

        #  split params into admin_user and code_user
        fdb = FalkorDB()  # (**self.cyp_config.auth_params)
        return fdb.select_graph(name)
