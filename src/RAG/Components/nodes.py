import pandas as pd

from src.ETL.Config.graph_pool import GraphPool
from src.RAG.Components.state import GRState

from src.Logging.logger import log_flk
from src.Exception.exception import LogException


class Nodes:
    def __init__(self, state: GRState):
        pass

    def guardrail(self, state: GRState):
        pass

    def user_memory(self, state: GRState):
        pass

    def super_agent(self, state: GRState):
        pass

    def query_agent(self, state: GRState):
        pass

    def tool_box(self, state: GRState):
        pass

    def query_graph(self, state: GRState):
        try:
            graph = GraphPool.get_graph(graph_name="test")
            result = graph.query(state.query, state.params)
            df = pd.DataFrame(
                data=result.result_set,
                columns=[item[-1] for item in result.header],
            )
            df = df.map(
                lambda row: ", ".join(str(item) for item in row)
                if isinstance(row, list)
                else row
            )
            data = df.to_dict(orient="list")

        except Exception as e:
            LogException(e, logger=log_flk)
            log_flk.info(f"Error:\n{state.query = }\n{state.params = }\n{e = }")
            data = {
                "message": f"Query:\n{state.query = }\nParams:\n{state.params = }\nError:\n{e = }"
            }

        return data
