from typing import Literal, Set
from pydantic import BaseModel, Field


class GetCompetitorDataModels:
    class QueryParams(BaseModel):
        area: str = Field(default="Koramangala", description="")
        cuisine: str = Field(default="Thai", description="")
        min_rating: float = Field(default=4.0, ge=0.0, le=5.0, description="")
        limit: int = Field(default=200, ge=1, le=2000, description="")

    class FunctionParams(BaseModel):
        q_params: "GetCompetitorDataModels.QueryParams" = Field(description="")
        output: Literal["dict", "dataframe"] = Field(default="dict", description="")


class GetCompetitorMenuModels:
    class QueryParams(BaseModel):
        area: str = Field(default="Koramangala", description="")
        cuisine: str = Field(default="Thai", description="")
        min_menu_rating: float = Field(default=4.0, ge=0.0, le=5.0, description="")
        limit: int = Field(default=200, ge=1, le=2000, description="")

    class FunctionParams(BaseModel):
        q_params: "GetCompetitorMenuModels.QueryParams" = Field(description="")
        output: Literal["dict", "dataframe"] = Field(default="dict", description="")


class GetMenuBenchmarkModels:
    class QueryParams(BaseModel):
        area: str = Field(default="Koramangala", description="")
        cuisine: str = Field(default="South Indian", description="")
        menu_name: str = Field(default="Masala Dosa", description="")
        limit: int = Field(default=200, ge=1, le=2000, description="")

    class FunctionParams(BaseModel):
        q_params: "GetMenuBenchmarkModels.QueryParams" = Field(description="")
        output: Literal["dict", "dataframe"] = Field(default="dict", description="")


class GetMenuOpportunitiesModels:
    class QueryParams(BaseModel):
        area: str = Field(default="Koramangala", description="")
        cuisine: str = Field(default="South Indian", description="")
        min_menu_rating: float = Field(default=4.0, ge=0.0, le=5.0, description="")
        limit: int = Field(default=200, ge=1, le=2000, description="")

    class FunctionParams(BaseModel):
        q_params: "GetMenuOpportunitiesModels.QueryParams" = Field(description="")
        output: Literal["dict", "dataframe"] = Field(default="dict", description="")


class GetOverpricedMenuModels:
    class QueryParams(BaseModel):
        area: str = Field(default="Koramangala", description="")
        cuisine: str = Field(default="South Indian", description="")
        min_listings: int = Field(default=2, ge=1, le=20, description="")
        max_avg_rating: float = Field(default=4.0, ge=0.0, le=5.0, description="")
        limit: int = Field(default=200, ge=1, le=2000, description="")

    class FunctionParams(BaseModel):
        q_params: "GetOverpricedMenuModels.QueryParams" = Field(description="")
        output: Literal["dict", "dataframe"] = Field(default="dict", description="")


class GetPremiumMenuModels:
    class QueryParams(BaseModel):
        area: str = Field(default="Koramangala", description="")
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
        area: str = Field(default="Koramangala", description="")
        cuisine: str = Field(default="South Indian", description="")
        min_menu_rating: float = Field(default=4.0, ge=1.0, le=5.0, description="")
        limit: int = Field(default=200, ge=1, le=2000, description="")

    class FunctionParams(BaseModel):
        q_params: "RecommendMenuModels.QueryParams" = Field(description="")
        output: Literal["dict", "dataframe"] = Field(default="dict", description="")
