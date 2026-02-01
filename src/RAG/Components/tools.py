import pandas as pd
from typing import Literal, Dict, Any, Hashable

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
                    'min_rating': 4.0,
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
        df = pd.DataFrame()
        try:
            q_code = self.cp_config.cp_code.tools[key]
            result = self.graph.query(q_code, q_params, timeout=1000)
            df = pd.DataFrame(
                data=result.result_set,
                columns=[item[-1] for item in result.header],
            )
            df = df.map(
                lambda row: ", ".join(str(item) for item in row)
                if isinstance(row, list)
                else row
            )

        except Exception as e:
            LogException(e, logger=log_flk)
            log_flk.info(f"Error:\n{q_code = }\n{q_params = }\n{e = }")

        return df if output == "dataframe" else df.to_dict(orient="list")

    def _get_area_cuisine_from_db(
        self,
        city_name: str | None,
        area_name: str | None,
        cuis_name: str | None,
        purpose: Literal["get_area_ids", "get_cuisine_name"] = "get_area_ids",
    ):
        """Method that returns area_id for a given city name-area name or cuisine name for a given name.

        Args:
            city_name (str | None): User requested city name.
            area_name (str | None): User requested area name.
            cuis_name (str | None): User requested cuisine name.
            purpose (Literal["get_area_ids", "get_cuisine_name"], optional): Which function to call. Defaults to "get_area_ids".

        Returns:
            parameter (str): area_ids or cuisine name to enter as parameter for toolbox functions.
        """
        try:
            q_code = self.cp_config.cp_code.gdb[purpose]

            if purpose == "get_area_ids":
                q_params = {
                    "city_name": city_name,
                    "area_name": area_name,
                }
            elif purpose == "get_cuisine_name":
                q_params = {"cuis_name": cuis_name}

            result = self.graph.query(q_code, q_params).result_set[0][0]

        except Exception as e:
            LogException(e, logger=log_flk)
            log_flk.info(f"Error:\n{q_code = }\n{q_params = }\n{e = }")
            result = {
                "message": f"Query:\n{q_code = }\nParams:\n{q_params = }\nError:\n{e = }"
            }

        return result
