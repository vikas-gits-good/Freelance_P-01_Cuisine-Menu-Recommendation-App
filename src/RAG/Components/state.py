import pandas as pd
from typing import Annotated, List, Literal, Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage
from langgraph.graph.message import add_messages


class GRState(BaseModel):
    """Main state for the GraphRAG workflow."""

    # Conversation tracking
    conversation: Annotated[List[AnyMessage], add_messages] = Field(
        default_factory=list,
        description="All messages for state tracking",
    )
    messages: Annotated[List[HumanMessage | AIMessage], add_messages] = Field(
        default_factory=list,
        description="Recent conversation messages for state tracking",
    )
    msg_summary: str = Field(
        default="Unavailable",
        description="Summary of conversation between user and planner agent",
    )

    # Guardrail Agent
    is_safe: bool = Field(
        default=True,
        description="Is the user query safe to proceed?",
    )
    guardrail_message: str = Field(
        default="Safe to proceed",
        description="Guardrail agent safety decision justification",
    )

    # User Memory
    user_preferences: str = Field(
        default="Unavailable",
        description="user preferences from memory",
    )
    user_summary: str = Field(
        default="Unavailable",
        description="user interest/plan summary from meory",
    )

    # Current turn
    user_query: Optional[HumanMessage] = Field(
        default=None,
        description="Current user query",
    )
    agent_answer: Optional[AIMessage] = Field(
        default=None,
        description="Current ai agent response",
    )

    # Planner Agent
    intent: Literal[
        "tool_call",
        "direct_db_query",
        "follow_up",
        "general_chat",
    ] = Field(
        default="general_chat",
        description="Planner decision on how to handle user query",
    )
    selected_tool: Optional[str] = Field(
        default=None,
        description="name of function to be called if decision is tool_call",
    )

    # Executor Agent
    func_parm_schm: Optional[BaseModel] = Field(
        default=None,
        description="Parameters as a schema for tool_call",
    )
    db_query_list: Optional[List[str]] = Field(
        default=None,
        description="list of db queries executed",
    )
    data_from_fkdb: Optional[Dict[str, Any] | pd.DataFrame] = Field(
        default=None,
        description="Data queried directly from falkordb",
    )

    # Toolbox
    tool_result: Dict[str, Any] | pd.DataFrame = Field(
        default=pd.DataFrame(),
        description="Result obtained from toolbox functions",
    )

    # Flow control
    status: Literal[
        "success",
        "error",
        "needs_clarification",
        "in_progress",
    ] = Field(default="in_progress")
    error_message: str = Field(default="")
