from typing import Literal, Optional
from pydantic import BaseModel, Field, model_validator

# =============================================================================
# Guardrail Agent Models (for structured output)
# =============================================================================


class GuardrailSchema(BaseModel):
    is_safe: bool = Field(default=True)
    guardrail_message: str = Field(
        default="",
        description="A brief 5 to 20 word reasoning for user query classification",
    )


# =============================================================================
# Planner Agent Models (for structured output)
# =============================================================================


class IntentClassification(BaseModel):
    """Model for classifying user intent."""

    intent: Literal["tool_call", "direct_db_query", "follow_up", "general_chat"] = (
        Field(description="The classified intent of the user query")
    )
    reasoning: str = Field(
        description="Brief explanation of why this intent was chosen"
    )
    requires_clarification: bool = Field(
        default=False, description="Whether more info is needed from user"
    )
    clarification_question: Optional[str] = Field(
        default="Could you please provide more details?",
        description="Question to ask user if clarification needed",
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
    area_name: Optional[str] = Field(default=None, description="Area mentioned by user")
    cuisine_name: Optional[str] = Field(
        default=None, description="Cuisine type mentioned by user"
    )
    menu_name: Optional[str] = Field(
        default=None, description="Specific dish name if mentioned"
    )
    restaurant_name: Optional[str] = Field(
        default=None, description="Specific restaurant if mentioned"
    )
    min_rating: Optional[float] = Field(
        default=None, ge=0.0, le=5.0, description="Minimum rating filter"
    )
    limit: Optional[int] = Field(default=200, ge=1, le=2000, description="Result limit")


class PlannerOutput(BaseModel):
    """Combined output from the Planner Agent."""

    intent: IntentClassification
    tool_selection: Optional[ToolSelection] = None
    extracted_params: ExtractedParams


# =============================================================================
# Executor Agent Models
# =============================================================================
class CypherQueryPlan(BaseModel):
    """Model for direct DB query planning."""

    query: str = Field(description="Cypher query to execute")
    purpose: str = Field(description="What this query retrieves")


# =============================================================================
# Tool Function Parameter Models
# =============================================================================
class _QP_get_comp_data(BaseModel):
    area_ids: str = Field(default="", description="always return ''")
    cuisine: str = Field(default="", description="always return ''")
    min_cmpt_rating: float = Field(
        default=4.0,
        ge=0.0,
        le=5.0,
        description="minimum restaurant rating",
    )
    limit: int = Field(
        default=200, ge=20, le=2000, description="number of records to retrieve"
    )


class _QP_get_comp_menu(BaseModel):
    area_ids: str = Field(default="", description="always return ''")
    cuisine: str = Field(default="", description="always return ''")
    min_menu_rating: float = Field(
        default=4.0, ge=0.0, le=5.0, description=" minimum menu rating"
    )
    num_per_rstn: int = Field(
        default=50, ge=20, le=100, description="number of menu items per restaurant"
    )
    limit: int = Field(
        default=500, ge=100, le=2000, description="number of records to retrieve"
    )


class _QP_get_menu_bnch_mark(BaseModel):
    area_ids: str = Field(default="", description="always return ''")
    cuisine: str = Field(default="", description="always return ''")
    menu_name: str = Field(
        default="Masala Dosa", description="name of the menu item from user"
    )
    limit: int = Field(
        default=200, ge=10, le=2000, description="number of records to retrieve"
    )


class _QP_get_menu_oppr(BaseModel):
    area_ids: str = Field(default="", description="always return ''")
    cuisine: str = Field(default="", description="always return ''")
    min_menu_rating: float = Field(
        default=4.0, ge=0.0, le=5.0, description="minimum menu rating"
    )
    limit: int = Field(
        default=200, ge=1, le=2000, description="number of records to retrieve"
    )


class _QP_get_ovpr_menu(BaseModel):
    area_ids: str = Field(default="", description="always return ''")
    cuisine: str = Field(default="", description="always return ''")
    min_listings: int = Field(
        default=2,
        ge=1,
        le=20,
        description="minimum number of restaurants serving same dish",
    )
    max_avg_rating: float = Field(
        default=4.0,
        ge=0.0,
        le=5.0,
        description="maximum average rating of same dish across restaurants",
    )
    limit: int = Field(
        default=200, ge=1, le=2000, description="number of records to retrieve"
    )


class _QP_get_prem_menu(BaseModel):
    area_ids: str = Field(default="", description="always return ''")
    cuisine: str = Field(default="", description="always return ''")
    min_listings: int = Field(
        default=2,
        ge=1,
        le=20,
        description="minimum number of restaurants serving same dish",
    )
    min_avg_rating: float = Field(
        default=4.3,
        ge=0.0,
        le=5.0,
        description="minimum average rating of same dish across restaurants",
    )
    limit: int = Field(
        default=200, ge=1, le=2000, description="number of records to retrieve"
    )


class _QP_get_spec_cmpt_menu(BaseModel):
    rstn_id: int = Field(default=418, description="always return 418")
    limit: int = Field(
        default=200, ge=100, le=2000, description="number of records to retrieve"
    )


class _QP_get_rcmd_menu(BaseModel):
    area_ids: str = Field(default="", description="always return ''")
    cuisine: str = Field(default="", description="always return ''")
    min_menu_rating: float = Field(
        default=4.0, ge=1.0, le=5.0, description="minimum rating for each dish"
    )
    limit: int = Field(
        default=200, ge=1, le=2000, description="number of records to retrieve"
    )


class _ToolFuncModel(BaseModel):
    output: Literal["dict", "dataframe"] = "dict"  # LangStudio supports df

    @model_validator(mode="before")
    @classmethod
    def trfm(cls, data: dict):
        return {"q_params": data, "output": "dict"}


class GetCompetitorDataModels(_ToolFuncModel):
    q_params: _QP_get_comp_data


class GetCompetitorMenuModels(_ToolFuncModel):
    q_params: _QP_get_comp_menu


class GetMenuBenchmarkModels(_ToolFuncModel):
    q_params: _QP_get_menu_bnch_mark


class GetMenuOpportunitiesModels(_ToolFuncModel):
    q_params: _QP_get_menu_oppr


class GetOverpricedMenuModels(_ToolFuncModel):
    q_params: _QP_get_ovpr_menu


class GetPremiumMenuModels(_ToolFuncModel):
    q_params: _QP_get_prem_menu


class GetSpecificCompetitorMenuModels(_ToolFuncModel):
    q_params: _QP_get_spec_cmpt_menu


class GetRecommendMenuModels(_ToolFuncModel):
    q_params: _QP_get_rcmd_menu
