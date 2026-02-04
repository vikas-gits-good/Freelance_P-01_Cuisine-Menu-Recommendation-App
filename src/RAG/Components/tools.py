from typing import Literal
from langchain_core.tools import tool

from src.RAG.Config.tool_funcs import CypherFunctionTool
from src.RAG.Config.tool_models import (
    GetCompetitorDataModels,
    GetCompetitorMenuModels,
    GetMenuBenchmarkModels,
    GetMenuOpportunitiesModels,
    GetOverpricedMenuModels,
    GetPremiumMenuModels,
    GetSpecificCompetitorMenuModels,
    GetRecommendMenuModels,
)


cft = CypherFunctionTool()


@tool
def get_competitors_data(param_model: GetCompetitorDataModels):
    return cft.get_competitors_data(**param_model.model_dump())


@tool
def get_competitors_menu(param_model: GetCompetitorMenuModels):
    return cft.get_competitors_menu(**param_model.model_dump())


@tool
def get_menu_benchmark(param_model: GetMenuBenchmarkModels):
    return cft.get_menu_benchmark(**param_model.model_dump())


@tool
def get_menu_opportunities(param_model: GetMenuOpportunitiesModels):
    return cft.get_menu_opportunities(**param_model.model_dump())


@tool
def get_overpriced_menu(param_model: GetOverpricedMenuModels):
    return cft.get_overpriced_menu(**param_model.model_dump())


@tool
def get_premium_menu(param_model: GetPremiumMenuModels):
    return cft.get_premium_menu(**param_model.model_dump())


@tool
def get_specific_competitor_menu(param_model: GetSpecificCompetitorMenuModels):
    return cft.get_specific_competitor_menu(**param_model.model_dump())


@tool
def recommend_menu(param_model: GetRecommendMenuModels):
    return cft.recommend_menu(**param_model.model_dump())


@tool
def query_database(query):
    """Method that queries falkordb and returns data

    Args:
        query (str): opencypher 9 query to get data

    Returns:
        data (dict): Requested data in dictionary format
    """
    return cft._query_falkordb(query)


@tool
def get_params(
    city_name: str | None = None,
    area_name: str | None = None,
    cuis_name: str | None = None,
    rstn_name: str | None = None,
    purpose: Literal["get_area_ids", "get_cuis_name", "get_rstn_ids"] = "get_area_ids",
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
    return cft._get_params_from_db(city_name, area_name, cuis_name, rstn_name, purpose)
