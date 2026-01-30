import pandas as pd
from typing import Literal, Dict, Any

from src.ETL.Config.graph_pool import GraphPool
from src.RAG.Config import CypherCodeConfig

from src.Logging.logger import log_flk
from src.Exception.exception import LogException, CustomException


class CypherFunctionTool:
    def __init__(self, cp_config: CypherCodeConfig = CypherCodeConfig()):
        try:
            self.graph = GraphPool.get_graph(graph_name="test")
            self.tools_list = [
                self.get_competitors_data,
                # is there a class iterable method to get function names as callables?
            ]
            self.cp_config = cp_config

        except Exception as e:
            LogException(e, logger=log_flk)
            # raise CustomException(e)

    def get_competitors_data(
        self,
        q_params: dict,
        output: Literal["dict", "dataframe"] = "dict",
    ) -> Dict[str, Any] | pd.DataFrame:
        """Tool that queries FalkorDB and returns competitors' basic data in a given area and cuisine.
        ## Usage:
        ```python
            func_params = {
                'q_params': {
                    "area": "Indiranagar",
                    "cuisine": "Thai",
                    "limit": 200,
                },
                "output": "dict",
            }
        data = get_competitors_data(**func_params)
        ```
        Args:
            q_params (dict): Parameters to pass into graph query.
            output (Literal["dict", "dataframe"], optional): Data output format. Defaults to "dict".

        Returns:
            Dict[str, Any] | pd.DataFrame: Competitors' basic data.
        """
        rqrd_data = {}
        try:
            graph_query = self.cp_config.cp_code.tools["cypher_get_competitors_data"]
            columns = self.cp_config.cp_cols.cols["cypher_get_competitors_data"]
            result = self.graph.query(graph_query, q_params).result_set
            rqrd_data = {
                key: [
                    ", ".join(str(item) for item in data[columns.index(key)])
                    if isinstance(data[columns.index(key)], list)
                    else data[columns.index(key)]
                    for data in result
                ]
                for key in columns
            }
        except Exception as e:
            LogException(e, logger=log_flk)
            # raise CustomException(e)

        return pd.DataFrame(rqrd_data) if output == "dataframe" else rqrd_data
