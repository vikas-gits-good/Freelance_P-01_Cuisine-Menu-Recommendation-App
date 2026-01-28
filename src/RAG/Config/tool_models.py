from typing import Literal, List
from pydantic import BaseModel, Field


class GetCompetitorModels:
    class QueryParams(BaseModel):
        area: str = Field(default="Koramangala", description="")
        cuisine: str = Field(default="Thai", description="")
        min_rating: float = Field(default=4.0, ge=0.0, le=5.0, description="")
        limit: int = Field(default=200, ge=1, le=2000, description="")

    class FunctionParams(BaseModel):
        q_params: "GetCompetitorModels.QueryParams" = Field(description="")
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
