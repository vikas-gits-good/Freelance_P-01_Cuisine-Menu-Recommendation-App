from typing import Literal, List
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
        exclude: List[
            Literal[
                "ids",
                "name",
                "city",
                "area",
                "locality",
                "cuisines",
                "rating",
                "address",
                "coords",
                "chain",
                "city_id",
            ]
        ] = Field(default=["ids", "city_id"], description="")


class GetCompetitorMenuModels:
    class QueryParams(BaseModel):
        area: str = Field(default="Koramangala", description="")
        cuisine: str = Field(default="Thai", description="")
        min_menu_rating: float = Field(default=4.0, ge=0.0, le=5.0, description="")
        limit: int = Field(default=200, ge=1, le=2000, description="")

    class FunctionParams(BaseModel):
        q_params: "GetCompetitorMenuModels.QueryParams" = Field(description="")
        output: Literal["dict", "dataframe"] = Field(default="dict", description="")
        exclude: List[
            Literal[
                "rstn_ids",
                "rstn_name",
                "rstn_city",
                "rstn_area",
                "rstn_locality",
                "rstn_cuisines",
                "rstn_rating",
                "rstn_address",
                "rstn_coords",
                "rstn_chain",
                "rstn_city_id",
                "food_name",
                "food_types",
                "food_price",
                "food_rating",
            ]
        ] = Field(default=["rstn_ids", "rstn_city_id"], description="")
