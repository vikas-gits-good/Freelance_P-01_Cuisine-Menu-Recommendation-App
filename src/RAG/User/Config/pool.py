from queue import Queue
from falkordb import FalkorDB
from falkordb.graph import Graph

from src.RAG.User.Config.cyphers import UserCypherConfig

GRAPH_NAME = "USER_KG"


class UserMemoryPool:
    """Connection pool for the user memory graph on FalkorDB DB 10."""

    def __init__(self, size: int = 2):
        self._pool = Queue(maxsize=size)
        for _ in range(size):
            self._pool.put(UserMemoryPool.get_graph())

    def acquire(self) -> Graph:
        """Blocks until a Graph is available."""
        return self._pool.get(block=True)

    def release(self, graph: Graph) -> None:
        """Returns a Graph to the pool. MUST be called in finally block."""
        self._pool.put(graph)

    @staticmethod
    def get_graph() -> Graph:
        """Returns a single Graph instance connected to USER_KG on DB 10."""
        ucc = UserCypherConfig()
        fdb = FalkorDB(**ucc.auth_params)
        return fdb.select_graph(GRAPH_NAME)
