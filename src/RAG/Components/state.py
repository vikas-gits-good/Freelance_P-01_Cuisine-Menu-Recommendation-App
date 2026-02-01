from typing import Annotated, List
from pydantic import BaseModel, Field
from langchain_core.messages import AnyMessage, HumanMessage
from langgraph.graph.message import add_messages


class MsgState(BaseModel):
    conversation: Annotated[List[AnyMessage], add_messages] = Field(
        default_factory=list,
        description="Full conversation of chat. Contains Human, AI, Tool Messages.",
    )


class RGState(BaseModel):
    user_query: HumanMessage
