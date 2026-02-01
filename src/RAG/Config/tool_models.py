from typing import Literal, Optional, Dict, Any, List
from pydantic import BaseModel, Field


# =============================================================================
# Planner Agent Models (for structured output)
# =============================================================================


class IntentClassification(BaseModel):
    """Model for classifying user intent."""

    intent: Literal["tool_call", "direct_db_query", "follow_up", "general_chat"] = Field(
        description="The classified intent of the user query"
    )
    reasoning: str = Field(description="Brief explanation of why this intent was chosen")
    requires_clarification: bool = Field(
        default=False, description="Whether more info is needed from user"
    )
    clarification_question: Optional[str] = Field(
        default=None, description="Question to ask user if clarification needed"
    )


class ToolSelection(BaseModel):
    """Model for selecting which tool to use."""

    tool_name: Literal[
        "get_competitors_data",
        "get_competitors_menu",
        "get_menu_benchmark",
        "get_menu_opportunities",
        "get_overpriced_menu",
        "get_premium_menu",
        "get_specific_competitor_menu",
        "recommend_menu",
    ] = Field(description="The tool to call based on user intent")
    reasoning: str = Field(description="Why this tool was selected")


class ExtractedParams(BaseModel):
    """Model for extracting raw parameters from user query."""

    city_name: Optional[str] = Field(default=None, description="City mentioned by user")
    area_name: Optional[str] = Field(default=None, description="Area/locality mentioned by user")
    cuisine_name: Optional[str] = Field(default=None, description="Cuisine type mentioned by user")
    menu_name: Optional[str] = Field(default=None, description="Specific dish name if mentioned")
    restaurant_name: Optional[str] = Field(default=None, description="Specific restaurant if mentioned")
    min_rating: Optional[float] = Field(default=None, ge=0.0, le=5.0, description="Minimum rating filter")
    limit: Optional[int] = Field(default=200, ge=1, le=2000, description="Result limit")


class PlannerOutput(BaseModel):
    """Combined output from the Planner Agent."""

    intent: IntentClassification
    tool_selection: Optional[ToolSelection] = None
    extracted_params: ExtractedParams


# =============================================================================
# Executor Agent Models
# =============================================================================


class ResolvedToolParams(BaseModel):
    """Final resolved parameters ready for tool execution."""

    area_ids: Optional[str] = Field(default=None, description="Resolved area_ids from DB")
    cuisine: Optional[str] = Field(default=None, description="Resolved cuisine name from DB")
    menu_name: Optional[str] = Field(default=None, description="Menu item name")
    rstn_id: Optional[int] = Field(default=None, description="Restaurant ID")
    min_rating: float = Field(default=4.0, ge=0.0, le=5.0)
    min_menu_rating: float = Field(default=4.0, ge=0.0, le=5.0)
    min_listings: int = Field(default=2, ge=1, le=20)
    min_avg_rating: float = Field(default=4.0, ge=0.0, le=5.0)
    max_avg_rating: float = Field(default=4.0, ge=0.0, le=5.0)
    limit: int = Field(default=200, ge=1, le=2000)


class CypherQueryPlan(BaseModel):
    """Model for direct DB query planning."""

    query: str = Field(description="Cypher query to execute")
    purpose: str = Field(description="What this query retrieves")


# =============================================================================
# Tool Function Parameter Models
# =============================================================================


class GetCompetitorDataModels:
    class QueryParams(BaseModel):
        area_ids: str = Field(
            default="area_Indiranagar__city_Bangalore-relation:7902476", description=""
        )
        cuisine: str = Field(default="Thai", description="")
        min_rating: float = Field(default=4.0, ge=0.0, le=5.0, description="")
        limit: int = Field(default=200, ge=1, le=2000, description="")

    class FunctionParams(BaseModel):
        q_params: "GetCompetitorDataModels.QueryParams" = Field(description="")
        output: Literal["dict", "dataframe"] = Field(default="dict", description="")


class GetCompetitorMenuModels:
    class QueryParams(BaseModel):
        area_ids: str = Field(
            default="area_Indiranagar__city_Bangalore-relation:7902476", description=""
        )
        cuisine: str = Field(default="Thai", description="")
        min_menu_rating: float = Field(default=4.0, ge=0.0, le=5.0, description="")
        num_per_rstn: int = Field(default=50, ge=20, le=100, description="")
        limit: int = Field(default=500, ge=100, le=2000, description="")

    class FunctionParams(BaseModel):
        q_params: "GetCompetitorMenuModels.QueryParams" = Field(description="")
        output: Literal["dict", "dataframe"] = Field(default="dict", description="")


class GetMenuBenchmarkModels:
    class QueryParams(BaseModel):
        area_ids: str = Field(
            default="area_Indiranagar__city_Bangalore-relation:7902476", description=""
        )
        cuisine: str = Field(default="South Indian", description="")
        menu_name: str = Field(default="Masala Dosa", description="")
        limit: int = Field(default=200, ge=1, le=2000, description="")

    class FunctionParams(BaseModel):
        q_params: "GetMenuBenchmarkModels.QueryParams" = Field(description="")
        output: Literal["dict", "dataframe"] = Field(default="dict", description="")


class GetMenuOpportunitiesModels:
    class QueryParams(BaseModel):
        area_ids: str = Field(
            default="area_Indiranagar__city_Bangalore-relation:7902476", description=""
        )
        cuisine: str = Field(default="South Indian", description="")
        min_menu_rating: float = Field(default=4.0, ge=0.0, le=5.0, description="")
        limit: int = Field(default=200, ge=1, le=2000, description="")

    class FunctionParams(BaseModel):
        q_params: "GetMenuOpportunitiesModels.QueryParams" = Field(description="")
        output: Literal["dict", "dataframe"] = Field(default="dict", description="")


class GetOverpricedMenuModels:
    class QueryParams(BaseModel):
        area_ids: str = Field(
            default="area_Indiranagar__city_Bangalore-relation:7902476", description=""
        )
        cuisine: str = Field(default="South Indian", description="")
        min_listings: int = Field(default=2, ge=1, le=20, description="")
        max_avg_rating: float = Field(default=4.0, ge=0.0, le=5.0, description="")
        limit: int = Field(default=200, ge=1, le=2000, description="")

    class FunctionParams(BaseModel):
        q_params: "GetOverpricedMenuModels.QueryParams" = Field(description="")
        output: Literal["dict", "dataframe"] = Field(default="dict", description="")


class GetPremiumMenuModels:
    class QueryParams(BaseModel):
        area_ids: str = Field(
            default="area_Indiranagar__city_Bangalore-relation:7902476", description=""
        )
        cuisine: str = Field(default="South Indian", description="")
        min_listings: int = Field(default=2, ge=1, le=20, description="")
        min_avg_rating: float = Field(default=4.0, ge=0.0, le=5.0, description="")
        limit: int = Field(default=200, ge=1, le=2000, description="")

    class FunctionParams(BaseModel):
        q_params: "GetPremiumMenuModels.QueryParams" = Field(description="")
        output: Literal["dict", "dataframe"] = Field(default="dict", description="")


class GetSpecificCompetitorMenuModels:
    class QueryParams(BaseModel):
        rstn_id: int = Field(default=418, description="")
        limit: int = Field(default=200, ge=1, le=2000, description="")

    class FunctionParams(BaseModel):
        q_params: "GetSpecificCompetitorMenuModels.QueryParams" = Field(description="")
        output: Literal["dict", "dataframe"] = Field(default="dict", description="")


class RecommendMenuModels:
    class QueryParams(BaseModel):
        area_ids: str = Field(
            default="area_Indiranagar__city_Bangalore-relation:7902476", description=""
        )
        cuisine: str = Field(default="South Indian", description="")
        min_menu_rating: float = Field(default=4.0, ge=1.0, le=5.0, description="")
        limit: int = Field(default=200, ge=1, le=2000, description="")

    class FunctionParams(BaseModel):
        q_params: "RecommendMenuModels.QueryParams" = Field(description="")
        output: Literal["dict", "dataframe"] = Field(default="dict", description="")
