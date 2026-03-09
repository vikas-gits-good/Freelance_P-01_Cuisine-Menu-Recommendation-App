from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(
        description="User query",
    )
    thread_id: Optional[str] = Field(
        default=None,
        description="Unique chat thread id",
    )


class ChatResponse(BaseModel):
    reply: str = Field(
        description="System response to user query",
    )
    thread_id: str = Field(
        description="Unique chat thread id",
    )
