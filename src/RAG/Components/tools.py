from typing import Any, Dict, Hashable, Literal, get_type_hints

import pandas as pd
from pydantic import BaseModel
from langchain_core.tools import tool, BaseTool

from src.RAG.Config.tool_funcs import CypherFunctionTool
from src.RAG.Config.tool_models import (
    GetCompetitorDataModels,
    GetCompetitorMenuModels,
    GetMenuBenchmarkModels,
    GetMenuOpportunitiesModels,
    GetOverpricedMenuModels,
    GetPremiumMenuModels,
    GetRecommendMenuModels,
    GetSpecificCompetitorMenuModels,
)

cft = CypherFunctionTool()


class DatabaseQueryTools:
    def __init__(self):
        self.db_tool_box_func: Dict[str, BaseTool] = {
            name: attr
            for name, attr in type(self).__dict__.items()
            if not name.startswith("_") and hasattr(attr, "func")
        }
        self.db_tool_box_schm: Dict[str, BaseModel] = {
            name: get_type_hints(tool_obj.func).get("param_model")
            for name, tool_obj in self.db_tool_box_func.items()
            if "param_model" in get_type_hints(tool_obj.func)
        }

    @tool
    @staticmethod
    def get_competitors_data(
        param_model: GetCompetitorDataModels,
    ) -> Dict[Hashable, Any] | pd.DataFrame:
        """Method to get data about competitors in a given area, city & cuisine

        Args:
            param_model (GetCompetitorDataModels): Pydantic model with function parameters

        Returns:
            data (Dict[Hashable, Any] | pd.DataFrame): Requested Data.
        """
        return cft.get_competitors_data(**param_model.model_dump())

    @tool
    @staticmethod
    def get_competitors_menu(param_model: GetCompetitorMenuModels):
        """Method to get menus of competitors in a given area, city & cuisine

        Args:
            param_model (GetCompetitorMenuModels): Pydantic model with function parameters

        Returns:
            data (Dict[Hashable, Any] | pd.DataFrame): Requested Data.
        """
        return cft.get_competitors_menu(**param_model.model_dump())

    @tool
    @staticmethod
    def get_menu_benchmark(param_model: GetMenuBenchmarkModels):
        """Method to get data to benchmark a given menu from competitors in a given area, city, menu & cuisine

        Args:
            param_model (GetMenuBenchmarkModels): Pydantic model with function parameters

        Returns:
            data (Dict[Hashable, Any] | pd.DataFrame): Requested Data.
        """
        return cft.get_menu_benchmark(**param_model.model_dump())

    @tool
    @staticmethod
    def get_menu_opportunities(param_model: GetMenuOpportunitiesModels):
        """Method to get data to benchmark a given menu from competitors in a given area, city & cuisine

        Args:
            param_model (GetMenuOpportunitiesModels): Pydantic model with function parameters

        Returns:
            data (Dict[Hashable, Any] | pd.DataFrame): Requested Data.
        """
        return cft.get_menu_opportunities(**param_model.model_dump())

    @tool
    @staticmethod
    def get_overpriced_menu(param_model: GetOverpricedMenuModels):
        """Method to get data on overpriced menus from competitors in a given area, city & cuisine

        Args:
            param_model (GetOverpricedMenuModels): Pydantic model with function parameters

        Returns:
            data (Dict[Hashable, Any] | pd.DataFrame): Requested Data.
        """
        return cft.get_overpriced_menu(**param_model.model_dump())

    @tool
    @staticmethod
    def get_premium_menu(param_model: GetPremiumMenuModels):
        """Method to get data on premium menus from competitors in a given area, city & cuisine

        Args:
            param_model (GetOverpricedMenuModels): Pydantic model with function parameters

        Returns:
            data (Dict[Hashable, Any] | pd.DataFrame): Requested Data.
        """
        return cft.get_premium_menu(**param_model.model_dump())

    @tool
    @staticmethod
    def get_specific_competitor_menu(param_model: GetSpecificCompetitorMenuModels):
        """Method to get full menu from a specified competitor in a given area, city

        Args:
            param_model (GetOverpricedMenuModels): Pydantic model with function parameters

        Returns:
            data (Dict[Hashable, Any] | pd.DataFrame): Requested Data.
        """
        return cft.get_specific_competitor_menu(**param_model.model_dump())

    @tool
    @staticmethod
    def recommend_menu(param_model: GetRecommendMenuModels):
        """Method to get all menu items above a certain rating from
        all competitors restaurant in a given area, city and cuisine.

        Args:
            param_model (GetOverpricedMenuModels): Pydantic model with function parameters

        Returns:
            data (Dict[Hashable, Any] | pd.DataFrame): Requested Data.
        """
        return cft.recommend_menu(**param_model.model_dump())

    @tool
    @staticmethod
    def _query_falkordb(query):
        """Method that queries falkordb and returns data

        Args:
            query (str): opencypher 9 query to get data

        Returns:
            data (dict): Requested data in dictionary format
        """
        return cft._query_falkordb(query)

    @tool
    @staticmethod
    def _get_params_from_db(
        city_name: str | None = None,
        area_name: str | None = None,
        cuis_name: str | None = None,
        rstn_name: str | None = None,
        purpose: Literal[
            "get_area_ids", "get_cuis_name", "get_rstn_ids"
        ] = "get_area_ids",
    ):
        """Method that returns area ids, cuisine name or restaurant id.

        Args:
            city_name (str | None): User requested city name. Default None.
            area_name (str | None): User requested area name. Default None.
            cuis_name (str | None): User requested cuisine name. Default None.
            rstn_name (str | None): User requested restaurant name. Default None.
            purpose (Literal["get_area_ids", "get_cuis_name", "get_rstn_ids"], optional): Which function to call. Defaults to "get_area_ids".

        Returns:
            parameter (str): area ids, cuisine name or restaurant id to enter as parameter for toolbox functions.
        """
        _locals = locals()
        purpose_params = {
            "get_area_ids": ["city_name", "area_name"],
            "get_cuis_name": ["cuis_name"],
            "get_rstn_ids": ["city_name", "area_name", "rstn_name"],
        }
        q_params = {
            name: _locals[name]
            for name in purpose_params.get(purpose, [])
            if _locals[name] is not None
        }
        # always keep o/p format as dict as it will be unpacked by executor node
        return cft._process_data(q_params, output="dict", key=purpose)
