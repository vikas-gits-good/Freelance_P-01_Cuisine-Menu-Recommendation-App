from typing import Literal, Optional
from pydantic import BaseModel, Field, model_validator

from src.RAG.Constants.labels import PlannerLabels, ToolLabels

# =============================================================================
# Guardrail Agent Models (for structured output)
# =============================================================================


class GuardrailSchema(BaseModel):
    is_safe: bool = Field(
        default_factory=bool,
        description="is the user query safe?",
    )
    guardrail_message: str = Field(
        default_factory=str,
        description="A brief 10 to 30 word response to user explaining why their query is invalid",
    )


# =============================================================================
# User Memory Data (for structured output)
# =============================================================================


class UserPreferenceSchema(BaseModel):
    user_id: str = Field(
        default="Unavailable",
        description="unique user id",
    )
    user_preferences: str = Field(
        default="Unavailable",
        description="user preferences",
    )
    user_summary: str = Field(
        default="Unavailable",
        description="summary of user profile",
    )


# =============================================================================
# Planner Agent Models (for structured output)
# =============================================================================


class IntentClassification(BaseModel):
    """Model for classifying user intent."""  # Literal["tool_call", "daba_query", "gnrl_chat"]

    intent: PlannerLabels = Field(
        default=PlannerLabels.GNRL_CHAT,
        description="The classified intent of the user query as python Enum",
    )
    reasoning: str = Field(
        default_factory=str,
        description="Brief explanation of why this intent was chosen",
    )
    requires_clarification: bool = Field(
        default=False,
        description="Whether more info is needed from user",
    )
    clarification_question: Optional[str] = Field(
        default=None,
        description="Question to ask user if clarification needed in not more than 30 words",
    )


class ToolSelection(BaseModel):
    """Model for selecting which tool to use."""

    tool_name: ToolLabels = Field(
        default=ToolLabels.GET_COMPETITORS_DATA,
        description="The tool to call based on user intent as python Enum",
    )
    reasoning: str = Field(
        default_factory=str,
        description="Why this tool was selected",
    )


class PlannerOutput(BaseModel):
    """Combined output from the Planner Agent."""

    intent: IntentClassification
    tool_selection: Optional[ToolSelection] = None


# =============================================================================
# ToolBox Function Parameter Models
# =============================================================================
class _QP_get_comp_data(BaseModel):
    area_ids: str = Field(
        default="",
        description="always return ''",
    )
    cuisine: str = Field(
        default="",
        description="always return ''",
    )
    min_cmpt_rating: float = Field(
        default=4.0,
        ge=0.0,
        le=5.0,
        description="minimum restaurant rating",
    )
    limit: int = Field(
        default=200,
        ge=20,
        le=2000,
        description="number of records to retrieve",
    )


class _QP_get_comp_menu(BaseModel):
    area_ids: str = Field(
        default="",
        description="always return ''",
    )
    cuisine: str = Field(
        default="",
        description="always return ''",
    )
    min_menu_rating: float = Field(
        default=4.0,
        ge=0.0,
        le=5.0,
        description=" minimum menu rating",
    )
    num_per_rstn: int = Field(
        default=50,
        ge=20,
        le=100,
        description="number of menu items per restaurant",
    )
    limit: int = Field(
        default=500,
        ge=100,
        le=2000,
        description="number of records to retrieve",
    )


class _QP_get_menu_bnch_mark(BaseModel):
    area_ids: str = Field(
        default="",
        description="always return ''",
    )
    cuisine: str = Field(
        default="",
        description="always return ''",
    )
    menu_name: str = Field(
        default="Masala Dosa",
        description="name of the menu item from user",
    )
    limit: int = Field(
        default=200,
        ge=10,
        le=2000,
        description="number of records to retrieve",
    )


class _QP_get_menu_oppr(BaseModel):
    area_ids: str = Field(
        default="",
        description="always return ''",
    )
    cuisine: str = Field(
        default="",
        description="always return ''",
    )
    min_menu_rating: float = Field(
        default=4.0,
        ge=0.0,
        le=5.0,
        description="minimum menu rating",
    )
    limit: int = Field(
        default=200,
        ge=1,
        le=2000,
        description="number of records to retrieve",
    )


class _QP_get_ovpr_menu(BaseModel):
    area_ids: str = Field(
        default="",
        description="always return ''",
    )
    cuisine: str = Field(
        default="",
        description="always return ''",
    )
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
        default=200,
        ge=1,
        le=2000,
        description="number of records to retrieve",
    )


class _QP_get_prem_menu(BaseModel):
    area_ids: str = Field(
        default="",
        description="always return ''",
    )
    cuisine: str = Field(
        default="",
        description="always return ''",
    )
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
        default=200,
        ge=1,
        le=2000,
        description="number of records to retrieve",
    )


class _QP_get_spec_cmpt_menu(BaseModel):
    rstn_id: int = Field(
        default=418,
        description="always return 418",
    )
    limit: int = Field(
        default=200,
        ge=100,
        le=2000,
        description="number of records to retrieve",
    )


class _QP_get_rcmd_menu(BaseModel):
    area_ids: str = Field(
        default="",
        description="always return ''",
    )
    cuisine: str = Field(
        default="",
        description="always return ''",
    )
    min_menu_rating: float = Field(
        default=4.0,
        ge=1.0,
        le=5.0,
        description="minimum rating for each dish",
    )
    limit: int = Field(
        default=200,
        ge=1,
        le=2000,
        description="number of records to retrieve",
    )


class _ToolFuncModel(BaseModel):
    output: Literal["dict", "dataframe"] = "dataframe"  # LangStudio supports df

    # @model_validator(mode="before")
    # @classmethod
    # def trfm(cls, data: dict):
    #     return {"q_params": data, "output": "dataframe"}

    @model_validator(mode="before")
    @classmethod
    def trfm(cls, data: dict):  # for langchain
        if "q_params" in data:
            return data
        return {"q_params": data, "output": "dataframe"}


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
