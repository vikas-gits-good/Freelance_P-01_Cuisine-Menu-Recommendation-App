import pandas as pd
from pydantic import BaseModel, Field, ConfigDict
from typing import Annotated, List, Dict, Any, Optional

from langchain_core.messages import AnyMessage, HumanMessage, AIMessage
from langgraph.graph.message import add_messages

from src.RAG.Constants.labels import PlannerLabels, StatusLabels, ToolLabels


class GRState(BaseModel):
    """Main state for the GraphRAG workflow."""

    # Conversation tracking
    messages: Annotated[List[HumanMessage | AIMessage], add_messages] = Field(
        default_factory=list,
        description="Chat conversation messages (Human + AI only)",
    )
    debug_convo: Annotated[List[AnyMessage], add_messages] = Field(
        default_factory=list,
        description="All messages for state tracking and debugging",
    )
    msg_summary: AIMessage = Field(
        default=AIMessage(content="Unavailable"),
        description="Summary of conversation between user and planner agent",
    )

    # Guardrail Agent
    is_safe: bool = Field(
        default_factory=bool,
        description="Is the user query safe to proceed?",
    )
    guardrail_message: str = Field(
        default_factory=str,
        description="A brief 10 to 30 word response to user explaining why their query is invalid",
    )

    # User Memory
    user_id: str = Field(
        default="Unavailable",
        description="unique user id",
    )
    session_id: str = Field(
        default="",
        description="current session id",
    )
    turn_count: int = Field(
        default=0,
        description="interaction turn counter within session",
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
    # user_query: Optional[HumanMessage] = Field(
    #     default=None,
    #     description="Current user query",
    # )
    # agent_answer: Optional[AIMessage] = Field(
    #     default=None,
    #     description="Current ai agent response",
    # )

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
    func_parm_schm: Optional[BaseModel] = Field(
        default=None,
        description="Parameters as a schema for tool_call",
    )
    # db_query_list: List[str] = Field(
    #     default_factory=list,
    #     description="list of db queries executed",
    # )
    data_from_fkdb: Optional[str] = Field(
        default="Unavailable",
        description="Data queried directly from falkordb",
    )

    # Toolbox
    # some bs pydantic compilation error
    # model_config = ConfigDict(arbitrary_types_allowed=True)
    # tool_result: Dict[str, Any] | pd.DataFrame = Field(
    #     default_factory=pd.DataFrame,
    #     description="Result obtained from toolbox functions",
    # )

    # Flow control
    status: StatusLabels = Field(
        default=StatusLabels.PROGRESS,
        description="Current status of the state for given query",
    )
    # error_message: str = Field(
    #     default_factory=str,
    #     description="Error message to end user incase of error in graph state",
    # )

    def reset_turn(self) -> None:
        """Reset per-turn state fields at the start of each invocation."""
        self.messages = [
            msg
            for msg in self.messages  # dont send tabular data to llm
            if not (
                isinstance(msg, AIMessage)
                and getattr(msg, "tool_call_id", None)
                == f"{PlannerLabels.TOOL_CALL.value}_data"
            )
        ]
        self.is_safe = False
        self.guardrail_message = ""
        # self.agent_answer = None
        self.intent = PlannerLabels.GNRL_CHAT
        self.selected_tool = None
        self.func_parm_schm = None
        # self.db_query_list = []
        self.data_from_fkdb = "Unavailable"
        self.status = StatusLabels.PROGRESS
        # self.error_message = ""
