from queue import Queue
from typing import Literal

from falkordb import FalkorDB
from falkordb.graph import Graph

from Src.Constants import ETLCyphersConstants

from .k_graph_config import FalkorDBConfig


class GraphPool:
    """Quick method to create Graph instances for concurrent purposes."""

    def __init__(
        self,
        size: int = 4,
        graph_name: Literal["prod", "devl", "test"] = "prod",
    ):
        self._pool = Queue(maxsize=size)

        for _ in range(size):
            self._pool.put(GraphPool.get_graph(graph_name))  # type: ignore

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
        graph_name: Literal["prod", "devl", "test"] = "prod",
    ) -> Graph:
        """Static Method that returns a single `Graph` instance.

        Args:
            graph_name (Literal["prod", "devl", "test"], optional): Name of the graph to return. Defaults to `"prod"`.

        Returns:
            graph (Graph): Single `Graph` object.
        """
        ecc = ETLCyphersConstants
        name = {
            "prod": ecc.KG_NAME_PROD,
            "devl": ecc.KG_NAME_DEVL,
            "test": ecc.KG_NAME_TEST,
        }.get(graph_name, ecc.KG_NAME_PROD)

        fdc = FalkorDBConfig()
        fdb = FalkorDB(**fdc.conn_dict)
        return fdb.select_graph(name)
