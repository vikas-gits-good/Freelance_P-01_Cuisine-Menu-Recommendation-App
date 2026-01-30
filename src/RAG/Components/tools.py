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
            self.cp_config = cp_config
            self.tools_list = [
                self.get_competitors_data,
                # is there a class iterable method to get function names as callables?
            ]

        except Exception as e:
            LogException(e, logger=log_flk)
            # raise CustomException(e)

    def get_competitors_data(
        self,
        q_params: dict,
        output: Literal["dict", "dataframe"] = "dict",
    ) -> Dict[str, Any] | pd.DataFrame:
        """Tool that queries FalkorDB and returns competitors' basic data in a
        given area and cuisine.
        ## Usage:
        ```python
            func_params = {
                "q_params": {
                    "area_ids": "area_Indiranagar__city_Bangalore-relation:7902476",
                    "cuisine": "Thai",
                    "limit": 200
                },
                "output": "dict"
            }
        data = get_competitors_data(**func_params)
        ```
        Args:
            q_params (dict): Parameters to pass into graph query.
            output (Literal["dict", "dataframe"], optional): Data output format. Defaults to "dict".

        Returns:
            Dict[str, Any] | pd.DataFrame: Competitors' `basic` data.
        """
        full_data = {}
        try:
            q_code = self.cp_config.cp_code.tools["cypher_get_competitors_data"]
            columns = self.cp_config.cp_cols.cols["cypher_get_competitors_data"]
            result = self.graph.query(q_code, q_params).result_set
            full_data = {
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
            log_flk.info(f"Error:\n{q_code = }\n{e = }")
            # raise CustomException(e)

        return pd.DataFrame(full_data) if output == "dataframe" else full_data

    def get_competitors_menu(
        self,
        q_params: dict,
        output: Literal["dict", "dataframe"] = "dict",
    ) -> Dict[str, Any] | pd.DataFrame:
        """Tool that queries FalkorDB and returns competitors' menu data in a
        given area and cuisine.
        ## Usage:
        ```python
            func_params = {
                "q_params": {
                    "area_ids": "area_Indiranagar__city_Bangalore-relation:7902476",
                    "cuisine": "Thai",
                    "min_menu_rating": 4.0,
                    "limit": 200
                },
                "output": "dict"
            }
        data = get_competitors_menu(**func_params)
        ```
        Args:
            q_params (dict): Parameters to pass into graph query.
            output (Literal["dict", "dataframe"], optional): Data output format.
            Defaults to "dict".

        Returns:
            Dict[str, Any] | pd.DataFrame: Competitors' `menu` data.
        """
        full_data = {}
        try:
            q_code = self.cp_config.cp_code.tools["cypher_get_competitors_menu"]
            columns = self.cp_config.cp_cols.cols["cypher_get_competitors_menu"]
            result = self.graph.query(q_code, q_params).result_set
            full_data = {
                f"{key1}_{key2}".replace("menu_", "food_", 1): [
                    (", ".join(str(item) for item in x) if isinstance(x, list) else x)
                    if (x := items[0][key1].get(key2, ""))
                    else False
                    for items in result
                ]
                for key1 in result[0][0].keys()
                for key2 in result[0][0][key1].keys()
                if f"{key1}_{key2}" not in columns
            }

        except Exception as e:
            LogException(e, logger=log_flk)
            log_flk.info(f"Error:\n{q_code = }\n{e = }")
            # raise CustomException(e)

        return pd.DataFrame(full_data) if output == "dataframe" else full_data

    def get_menu_benchmark(
        self,
        q_params: dict,
        output: Literal["dict", "dataframe"] = "dict",
    ) -> Dict[str, Any] | pd.DataFrame:
        """Tool that queries FalkorDB and returns competitors' data for a given dish
        in a given area and cuisine.
        ## Usage:
        ```python
            func_params = {
                "q_params": {
                    "area_ids": "area_Indiranagar__city_Bangalore-relation:7902476",
                    "cuisine": "South Indian",
                    "menu_name": "Masala Dosa",
                    "limit": 250
                },
                "output": "dict"
            }
        data = get_menu_benchmark(**func_params)
        ```
        Args:
            q_params (dict): Parameters to pass into graph query.
            output (Literal["dict", "dataframe"], optional): Data output format. Defaults to "dict".

        Returns:
            Dict[str, Any] | pd.DataFrame: Competitors' `menu` data.
        """
        full_data = {}
        try:
            q_code = self.cp_config.cp_code.tools["cypher_get_menu_benchmark"]
            columns = self.cp_config.cp_cols.cols["cypher_get_menu_benchmark"]
            result = self.graph.query(q_code, q_params).result_set
            full_data = {
                key: [item[columns.index(key)] for item in result] for key in columns
            }

        except Exception as e:
            LogException(e, logger=log_flk)
            log_flk.info(f"Error:\n{q_code = }\n{e = }")
            # raise CustomException(e)

        return pd.DataFrame(full_data) if output == "dataframe" else full_data

    def get_menu_opportunities(
        self,
        q_params: dict,
        output: Literal["dict", "dataframe"] = "dict",
    ) -> Dict[str, Any] | pd.DataFrame:
        """Tool that queries FalkorDB and returns competitors' data for a given dish
        in a given area and cuisine.
        ## Usage:
        ```python
            func_params = {
                "q_params": {
                    "area_ids": "area_Koramangala__city_Bangalore-relation:7902476",
                    "cuisine": "Thai",
                    "min_menu_rating": 4.0,
                    "limit": 250
                },
                "output": "dict"
            }
        data = get_menu_opportunities(**func_params)
        ```
        Args:
            q_params (dict): Parameters to pass into graph query.
            output (Literal["dict", "dataframe"], optional): Data output format. Defaults to "dict".

        Returns:
            Dict[str, Any] | pd.DataFrame: Competitors' `menu` data.
        """
        full_data = {}
        try:
            q_code = self.cp_config.cp_code.tools["cypher_get_menu_opportunities"]
            columns = self.cp_config.cp_cols.cols["cypher_get_menu_opportunities"]
            result = self.graph.query(q_code, q_params).result_set
            full_data = {
                key: [item[columns.index(key)] for item in result] for key in columns
            }

        except Exception as e:
            LogException(e, logger=log_flk)
            log_flk.info(f"Error:\n{q_code = }\n{e = }")
            # raise CustomException(e)

        return pd.DataFrame(full_data) if output == "dataframe" else full_data
