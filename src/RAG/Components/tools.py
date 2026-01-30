import pandas as pd
from typing import Literal, Dict, Any

from src.ETL.Config.graph_pool import GraphPool
from src.RAG.Config import CypherCodeConfig

from src.Logging.logger import log_flk
from src.Exception.exception import LogException


class CypherFunctionTool:
    def __init__(self, cp_config: CypherCodeConfig = CypherCodeConfig()):
        try:
            self.graph = GraphPool.get_graph(graph_name="test")
            self.cp_config = cp_config
            self.tools_list = [
                getattr(self, method_name)
                for method_name in dir(self)
                if not method_name.startswith("_")
                and callable(getattr(self, method_name))
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
                    'min_rating': 4.0,
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
            Dict[str, Any] | pd.DataFrame: Competitors' data.
        """
        full_data = {}
        try:
            full_data = self._process_data(q_params, "cypher_get_competitors_data")

        except Exception as e:
            LogException(e, logger=log_flk)

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
            Dict[str, Any] | pd.DataFrame: Competitors' data.
        """
        full_data = {}
        try:
            full_data = self._process_data(q_params, "cypher_get_competitors_menu")

        except Exception as e:
            LogException(e, logger=log_flk)

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
            Dict[str, Any] | pd.DataFrame: Competitors' data.
        """
        full_data = {}
        try:
            full_data = self._process_data(q_params, "cypher_get_menu_benchmark")

        except Exception as e:
            LogException(e, logger=log_flk)

        return pd.DataFrame(full_data) if output == "dataframe" else full_data

    def get_menu_opportunities(
        self,
        q_params: dict,
        output: Literal["dict", "dataframe"] = "dict",
    ) -> Dict[str, Any] | pd.DataFrame:
        """Tool that queries FalkorDB and returns data where food item is rated highly
        and few competitors serve it in a given area and cuisine.
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
            Dict[str, Any] | pd.DataFrame: Competitors' data.
        """
        full_data = {}
        try:
            full_data = self._process_data(q_params, "cypher_get_menu_opportunities")

        except Exception as e:
            LogException(e, logger=log_flk)

        return pd.DataFrame(full_data) if output == "dataframe" else full_data

    def get_overpriced_menu(
        self,
        q_params: dict,
        output: Literal["dict", "dataframe"] = "dict",
    ) -> Dict[str, Any] | pd.DataFrame:
        """Tool that queries FalkorDB and returns data where a given food item is overpriced
        in a given area and cuisine.
        ## Usage:
        ```python
            func_params = {
                "q_params": {
                    "area_ids": "area_Koramangala__city_Bangalore-relation:7902476",
                    "cuisine": "North Indian",
                    "min_listings": 5,
                    "max_avg_rating": 4.0,
                    "limit": 500
                },
                "output": "dict"
            }
        data = get_overpriced_menu(**func_params)
        ```
        Args:
            q_params (dict): Parameters to pass into graph query.
            output (Literal["dict", "dataframe"], optional): Data output format. Defaults to "dict".

        Returns:
            Dict[str, Any] | pd.DataFrame: Competitors' data.
        """
        full_data = {}
        try:
            full_data = self._process_data(q_params, "cypher_get_overpriced_menu")

        except Exception as e:
            LogException(e, logger=log_flk)

        return pd.DataFrame(full_data) if output == "dataframe" else full_data

    def get_premium_menu(
        self,
        q_params: dict,
        output: Literal["dict", "dataframe"] = "dict",
    ) -> Dict[str, Any] | pd.DataFrame:
        """Tool that queries FalkorDB and returns data where a given food item's price is high
        but there is proven demand in a given area and cuisine.
        ## Usage:
        ```python
            func_params = {
                "q_params": {
                    "area_ids": "area_Koramangala__city_Bangalore-relation:7902476",
                    "cuisine": "South Indian",
                    "min_listings": 1,
                    "min_avg_rating": 4.5,
                    "limit": 500
                },
                "output": "dict"
            }
        data = get_premium_menu(**func_params)
        ```
        Args:
            q_params (dict): Parameters to pass into graph query.
            output (Literal["dict", "dataframe"], optional): Data output format. Defaults to "dict".

        Returns:
            Dict[str, Any] | pd.DataFrame: Competitors' data.
        """
        full_data = {}
        try:
            full_data = self._process_data(q_params, "cypher_get_premium_menu")

        except Exception as e:
            LogException(e, logger=log_flk)

        return pd.DataFrame(full_data) if output == "dataframe" else full_data

    def get_specific_competitor_menu(
        self,
        q_params: dict,
        output: Literal["dict", "dataframe"] = "dict",
    ) -> Dict[str, Any] | pd.DataFrame:
        """Tool that queries FalkorDB and returns all menu items from a competitors restaurant
        in a given area.
        ## Usage:
        ```python
            func_params = {
                "q_params": {
                    "rstn_id": 418,
                    "limit": 200
                },
                "output": "dict"
            }
        data = get_specific_competitor_menu(**func_params)
        ```
        Args:
            q_params (dict): Parameters to pass into graph query.
            output (Literal["dict", "dataframe"], optional): Data output format. Defaults to "dict".

        Returns:
            Dict[str, Any] | pd.DataFrame: Competitors' data.
        """
        full_data = {}
        try:
            full_data = self._process_data(
                q_params, "cypher_get_specific_competitor_menu"
            )

        except Exception as e:
            LogException(e, logger=log_flk)

        return pd.DataFrame(full_data) if output == "dataframe" else full_data

    def recommend_menu(
        self,
        q_params: dict,
        output: Literal["dict", "dataframe"] = "dict",
    ) -> Dict[str, Any] | pd.DataFrame:
        """Tool that queries FalkorDB and returns all menu items above a certain rating from
        all competitors restaurant in a given area and cuisine.
        ## Usage:
        ```python
            func_params = {
                "q_params": {
                    "area_ids": 'area_Indiranagar__city_Bangalore-relation:7902476',
                    "cuisine": 'Continental',
                    "min_menu_rating": 4.0,
                    "limit": 300
                },
                "output": "dict"
            }
        data = recommend_menu(**func_params)
        ```
        Args:
            q_params (dict): Parameters to pass into graph query.
            output (Literal["dict", "dataframe"], optional): Data output format. Defaults to "dict".

        Returns:
            Dict[str, Any] | pd.DataFrame: Competitors' data.
        """
        full_data = {}
        try:
            full_data = self._process_data(q_params, "cypher_recommend_menu")

        except Exception as e:
            LogException(e, logger=log_flk)

        return pd.DataFrame(full_data) if output == "dataframe" else full_data

    def _process_data(self, q_params: dict, key: str):
        """Quick method to get make the database query and post process the data into required format

        Args:
            q_params (dict): The parameter dict of each function tool.
            key (str): A dictionary key string to get the cypher and column names.

        Returns:
            full_data (dict): The cleaned data from the FalkorDB.
        """
        full_data = {}
        try:
            q_code = self.cp_config.cp_code.tools[key]
            columns = self.cp_config.cp_cols.cols[key]
            result = self.graph.query(q_code, q_params).result_set

            if key == "cypher_get_competitors_data":
                full_data = {
                    key: [
                        ", ".join(str(item) for item in data[columns.index(key)])
                        if isinstance(data[columns.index(key)], list)
                        else data[columns.index(key)]
                        for data in result
                    ]
                    for key in columns
                }

            elif key == "cypher_get_competitors_menu":
                full_data = {
                    f"{key1}_{key2}".replace("menu_", "food_", 1): [
                        (
                            ", ".join(str(item) for item in x)
                            if isinstance(x, list)
                            else x
                        )
                        if (x := items[0][key1].get(key2)) is not None
                        else None
                        for items in result
                    ]
                    for key1 in result[0][0].keys()
                    for key2 in result[0][0][key1].keys()
                    if f"{key1}_{key2}" not in columns
                }

            else:
                full_data = {
                    key: [item[columns.index(key)] for item in result]
                    for key in columns
                }

        except Exception as e:
            LogException(e, logger=log_flk)
            log_flk.info(f"Error:\n{q_code = }\n{e = }")

        return full_data
