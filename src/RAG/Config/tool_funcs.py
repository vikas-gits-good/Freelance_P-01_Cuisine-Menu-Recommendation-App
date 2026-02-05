import pandas as pd
from typing import Any, Dict, Hashable, Literal

from src.ETL.Config.graph_pool import GraphPool
from src.RAG.Config.cypher import CypherCodeConfig

from src.Logging.logger import log_flk
from src.Exception.exception import LogException, CustomException


class CypherFunctionTool:
    def __init__(self, cp_config: CypherCodeConfig = CypherCodeConfig()):
        try:
            self.graph = GraphPool.get_graph(graph_name="test")
            self.cp_config = cp_config

        except Exception as e:
            LogException(e, logger=log_flk)
            # raise CustomException(e)

    def get_competitors_data(
        self,
        q_params: dict,
        output: Literal["dict", "dataframe"] = "dict",
    ) -> Dict[Hashable, Any] | pd.DataFrame:
        """Tool that queries FalkorDB and returns competitors' basic data in a
        given area and cuisine.
        ## Usage:
        ```python
        >>> from src.RAG.Components.tools import CypherFunctionTool
        >>> cft = CypherFunctionTool()
        >>> func_params = {
                "q_params": {
                    "area_ids": "area_Indiranagar__city_Bangalore-relation:7902476",
                    "cuisine": "Thai",
                    'min_cmpt_rating': 4.0,
                    "limit": 200
                },
                "output": "dict"
            }
        >>> data = cft.get_competitors_data(**func_params)
        ```
        Args:
            q_params (dict): Parameters to pass into graph query.
            output (Literal["dict", "dataframe"], optional): Data output format. Defaults to "dict".

        Returns:
            full_data (Dict[Hashable, Any] | pd.DataFrame): Competitors' data.
        """
        return self._process_data(q_params, output, self.get_competitors_data.__name__)

    def get_competitors_menu(
        self,
        q_params: dict,
        output: Literal["dict", "dataframe"] = "dict",
    ) -> Dict[Hashable, Any] | pd.DataFrame:
        """Tool that queries FalkorDB and returns competitors' menu data in a
        given area and cuisine.
        ## Usage:
        ```python
        >>> from src.RAG.Components.tools import CypherFunctionTool
        >>> cft = CypherFunctionTool()
        >>> func_params = {
                "q_params": {
                    "area_ids": "area_Indiranagar__city_Bangalore-relation:7902476",
                    "cuisine": "Thai",
                    "min_menu_rating": 4.0,
                    "limit": 200
                },
                "output": "dict"
            }
        >>> data = cft.get_competitors_menu(**func_params)
        ```
        Args:
            q_params (dict): Parameters to pass into graph query.
            output (Literal["dict", "dataframe"], optional): Data output format.
            Defaults to "dict".

        Returns:
            full_data (Dict[Hashable, Any] | pd.DataFrame): Competitors' data.
        """
        return self._process_data(q_params, output, self.get_competitors_menu.__name__)

    def get_menu_benchmark(
        self,
        q_params: dict,
        output: Literal["dict", "dataframe"] = "dict",
    ) -> Dict[Hashable, Any] | pd.DataFrame:
        """Tool that queries FalkorDB and returns competitors' data for a given dish
        in a given area and cuisine.
        ## Usage:
        ```python
        >>> from src.RAG.Components.tools import CypherFunctionTool
        >>> cft = CypherFunctionTool()
        >>> func_params = {
                "q_params": {
                    "area_ids": "area_Indiranagar__city_Bangalore-relation:7902476",
                    "cuisine": "South Indian",
                    "menu_name": "Masala Dosa",
                    "limit": 250
                },
                "output": "dict"
            }
        >>> data = cft.get_menu_benchmark(**func_params)
        ```
        Args:
            q_params (dict): Parameters to pass into graph query.
            output (Literal["dict", "dataframe"], optional): Data output format. Defaults to "dict".

        Returns:
            full_data (Dict[Hashable, Any] | pd.DataFrame): Competitors' data.
        """
        return self._process_data(q_params, output, self.get_menu_benchmark.__name__)

    def get_menu_opportunities(
        self,
        q_params: dict,
        output: Literal["dict", "dataframe"] = "dict",
    ) -> Dict[Hashable, Any] | pd.DataFrame:
        """Tool that queries FalkorDB and returns data where food item is rated highly
        and few competitors serve it in a given area and cuisine.
        ## Usage:
        ```python
        >>> from src.RAG.Components.tools import CypherFunctionTool
        >>> cft = CypherFunctionTool()
        >>> func_params = {
                "q_params": {
                    "area_ids": "area_Koramangala__city_Bangalore-relation:7902476",
                    "cuisine": "Thai",
                    "min_menu_rating": 4.0,
                    "limit": 250
                },
                "output": "dict"
            }
        >>> data = cft.get_menu_opportunities(**func_params)
        ```
        Args:
            q_params (dict): Parameters to pass into graph query.
            output (Literal["dict", "dataframe"], optional): Data output format. Defaults to "dict".

        Returns:
            full_data (Dict[Hashable, Any] | pd.DataFrame): Competitors' data.
        """
        return self._process_data(
            q_params, output, self.get_menu_opportunities.__name__
        )

    def get_overpriced_menu(
        self,
        q_params: dict,
        output: Literal["dict", "dataframe"] = "dict",
    ) -> Dict[Hashable, Any] | pd.DataFrame:
        """Tool that queries FalkorDB and returns data where a given food item is overpriced
        in a given area and cuisine.
        ## Usage:
        ```python
        >>> from src.RAG.Components.tools import CypherFunctionTool
        >>> cft = CypherFunctionTool()
        >>> func_params = {
                "q_params": {
                    "area_ids": "area_Koramangala__city_Bangalore-relation:7902476",
                    "cuisine": "North Indian",
                    "min_listings": 5,
                    "max_avg_rating": 4.0,
                    "limit": 500
                },
                "output": "dict"
            }
        >>> data = cft.get_overpriced_menu(**func_params)
        ```
        Args:
            q_params (dict): Parameters to pass into graph query.
            output (Literal["dict", "dataframe"], optional): Data output format. Defaults to "dict".

        Returns:
            full_data (Dict[Hashable, Any] | pd.DataFrame): Competitors' data.
        """
        return self._process_data(q_params, output, self.get_overpriced_menu.__name__)

    def get_premium_menu(
        self,
        q_params: dict,
        output: Literal["dict", "dataframe"] = "dict",
    ) -> Dict[Hashable, Any] | pd.DataFrame:
        """Tool that queries FalkorDB and returns data where a given food item's price is high
        but there is proven demand in a given area and cuisine.
        ## Usage:
        ```python
        >>> from src.RAG.Components.tools import CypherFunctionTool
        >>> cft = CypherFunctionTool()
        >>> func_params = {
                "q_params": {
                    "area_ids": "area_Koramangala__city_Bangalore-relation:7902476",
                    "cuisine": "South Indian",
                    "min_listings": 1,
                    "min_avg_rating": 4.5,
                    "limit": 500
                },
                "output": "dict"
            }
        >>> data = cft.get_premium_menu(**func_params)
        ```
        Args:
            q_params (dict): Parameters to pass into graph query.
            output (Literal["dict", "dataframe"], optional): Data output format. Defaults to "dict".

        Returns:
            full_data (Dict[Hashable, Any] | pd.DataFrame): Competitors' data.
        """
        return self._process_data(q_params, output, self.get_premium_menu.__name__)

    def get_specific_competitor_menu(
        self,
        q_params: dict,
        output: Literal["dict", "dataframe"] = "dict",
    ) -> Dict[Hashable, Any] | pd.DataFrame:
        """Tool that queries FalkorDB and returns all menu items from a competitors restaurant
        in a given area.
        ## Usage:
        ```python
        >>> from src.RAG.Components.tools import CypherFunctionTool
        >>> cft = CypherFunctionTool()
        >>> func_params = {
                "q_params": {
                    "rstn_id": 418,
                    "limit": 200
                },
                "output": "dict"
            }
        >>> data = cft.get_specific_competitor_menu(**func_params)
        ```
        Args:
            q_params (dict): Parameters to pass into graph query.
            output (Literal["dict", "dataframe"], optional): Data output format. Defaults to "dict".

        Returns:
            full_data (Dict[Hashable, Any] | pd.DataFrame): Competitors' data.
        """
        return self._process_data(
            q_params, output, self.get_specific_competitor_menu.__name__
        )

    def recommend_menu(
        self,
        q_params: dict,
        output: Literal["dict", "dataframe"] = "dict",
    ) -> Dict[Hashable, Any] | pd.DataFrame:
        """Tool that queries FalkorDB and returns all menu items above a certain rating from
        all competitors restaurant in a given area and cuisine.
        ## Usage:
        ```python
        >>> from src.RAG.Components.tools import CypherFunctionTool
        >>> cft = CypherFunctionTool()
        >>> func_params = {
                "q_params": {
                    "area_ids": 'area_Indiranagar__city_Bangalore-relation:7902476',
                    "cuisine": 'Continental',
                    "min_menu_rating": 4.0,
                    "limit": 300
                },
                "output": "dict"
            }
        >>> data = cft.recommend_menu(**func_params)
        ```
        Args:
            q_params (dict): Parameters to pass into graph query.
            output (Literal["dict", "dataframe"], optional): Data output format. Defaults to "dict".

        Returns:
            full_data (Dict[Hashable, Any] | pd.DataFrame): Competitors' data.
        """
        return self._process_data(q_params, output, self.recommend_menu.__name__)

    def _process_data(
        self,
        q_params: dict,
        output: Literal["dict", "dataframe"] = "dict",
        key: str = "",
    ) -> Dict[Hashable, Any] | pd.DataFrame:
        """Quick method to get make the database query and post process the data into required format
        ## Usage:
        ```python
        >>> full_data = self._process_data(q_params, output, self.recommend_menu.__name__)
        ```

        Args:
            q_params (dict): The parameter dict of each function tool.
            key (str): A dictionary key string to get the cypher and column names.

        Returns:
            full_data (Dict[str, Any]): The cleaned data from the FalkorDB.
        """
        try:
            q_code = self.cp_config.cp_code.tools[key]
            result = self.graph.query(q_code, q_params, timeout=1000)
            df = pd.DataFrame(
                data=result.result_set,
                columns=[item[-1] for item in result.header],
            )
            df = df.map(
                lambda row: (
                    ", ".join(str(item) for item in row)
                    if isinstance(row, list)
                    else row
                )
            )

        except Exception as e:
            LogException(e, logger=log_flk)
            log_flk.info(f"Error:\n{q_code = }\n{q_params = }\n{e = }")
            # This line goes directly to user. Dont include errors.
            df = pd.DataFrame()

        return df if output == "dataframe" else df.to_dict(orient="list")

    def _query_falkordb(
        self,
        query: str,
    ) -> Dict[Hashable, Any]:
        """Method to query FalkorDB and get data as a flattened dict.
        ## Usage:
        ```python
        >>> from src.RAG.Components.tools import CypherFunctionTool
        >>> cft = CypherFunctionTool()
        >>> query = "\nMATCH (cu:MainCuisine)\nWHERE toLower(cu.name) CONTAINS toLower('South Indian')\nRETURN cu.name AS cuisine_name\nLIMIT 1\n"
        >>> data = cft._query_falkordb(query)
        ```

        Args:
            query (dict): The query as a string to the database.

        Returns:
            data (Dict[Hashable, Any]): The flattened data from the FalkorDB.
        """
        try:
            result = self.graph.query(query, timeout=1000)
            df = pd.DataFrame(
                data=result.result_set,
                columns=[item[-1] for item in result.header],
            )
            df = df.map(
                lambda row: (
                    ", ".join(str(item) for item in row)
                    if isinstance(row, list)
                    else row
                )
            )

        except Exception as e:
            LogException(e, logger=log_flk)
            log_flk.info(f"Error:\n{query = }\n{e = }")
            df = pd.DataFrame({"query": query, "error": str(e)})

        return df.to_dict(orient="list")
