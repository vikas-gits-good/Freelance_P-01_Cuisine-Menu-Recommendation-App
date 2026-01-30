from typing import Annotated, List
from pydantic import BaseModel
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class GRState(BaseModel):
    conversation: Annotated[List[AnyMessage], add_messages]
