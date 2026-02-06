import pandas as pd
from pydantic import BaseModel, Field
from typing import List, Literal, Dict, Any, Optional

from langchain_core.messages import AnyMessage, HumanMessage, AIMessage, SystemMessage

from src.RAG.Constants.labels import PlannerLabels, StatusLabels, ToolLabels


class GRState(BaseModel):
    """Main state for the GraphRAG workflow."""

    # Conversation tracking
    conversation: List[AnyMessage] = Field(
        default_factory=list,
        description="All messages for state tracking",
    )
    messages: List[AnyMessage] = Field(
        default_factory=list,
        description="Recent conversation messages for state tracking",
    )
    msg_summary: AIMessage = Field(
        default=AIMessage(content="Unavailable"),
        description="Summary of conversation between user and planner agent",
    )

    # Guardrail Agent
    is_safe: bool = Field(
        default=False,
        description="Is the user query safe to proceed?",
    )
    guardrail_message: str = Field(
        default="Invalid query. Please limit queries to restaurants, menus and cuisines",
        description="A brief 10 to 30 word response to user explaining why their query is invalid",
    )

    # User Memory
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

    # Current turn
    user_query: HumanMessage = Field(
        default=HumanMessage(content="Unavailable"),
        description="Current user query",
    )
    agent_answer: AIMessage = Field(
        default=AIMessage(content="Unavailable"),
        description="Current ai agent response",
    )

    # Planner Agent
    intent: PlannerLabels = Field(
        default=PlannerLabels.GNRL_CHAT,
        description="Planner decision on how to handle user query",
    )
    selected_tool: Optional[ToolLabels] = Field(
        default=None,
        description="name of function to be called if decision is tool_call",
    )

    # Executor Agent
    func_parm_schm: BaseModel = Field(
        default=BaseModel(),
        description="Parameters as a schema for tool_call",
    )
    db_query_list: List[str] = Field(
        default=[],
        description="list of db queries executed",
    )
    data_from_fkdb: str = Field(
        default="Unavailable",
        description="Data queried directly from falkordb",
    )

    # Toolbox
    tool_result: Dict[str, Any] | pd.DataFrame = Field(
        default=pd.DataFrame(),
        description="Result obtained from toolbox functions",
    )

    # Flow control
    status: StatusLabels = Field(
        default=StatusLabels.PROGRESS,
        description="Current status of the state for given query",
    )
    error_message: str = Field(
        default="Sorry, there was an internal error. Can you repeat the question?",
        description="Error message to end user incase of error in graph state",
    )
