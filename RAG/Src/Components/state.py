from typing import Annotated, Any, Dict, List, Literal, Optional

import pandas as pd
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

from Src.Constants import PlannerLabels, StatusLabels, ToolLabels


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
    db_query_list: List[str] = Field(
        default_factory=list,
        description="list of db queries executed",
    )
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

    @staticmethod
    def remove_table(
        messages: List[HumanMessage | AIMessage],
        purpose: Literal["messages", "temporary"] = "temporary",
    ) -> List[HumanMessage | AIMessage]:
        """Remove AIMessages containing tabular tool_call data."""
        tag = f"{PlannerLabels.TOOL_CALL.value}_data"
        if purpose == "messages":
            # messages.extend(
            #     [
            #         RemoveMessage(msg.id)
            #         for msg in messages[:]
            #         if (
            #             isinstance(msg, AIMessage)
            #             and msg.additional_kwargs.get("tag") == tag
            #         )
            #     ]
            # )

            # messages[0:0] = [
            #     RemoveMessage(msg.id)
            #     for msg in messages[:]
            #     if (
            #         isinstance(msg, AIMessage)
            #         and msg.additional_kwargs.get("tag") == tag
            #     )
            # ]

            # for i, msg in enumerate(messages):
            #     if (
            #         isinstance(msg, AIMessage)
            #         and msg.additional_kwargs.get("tag") == tag
            #     ):
            #         messages[i] = RemoveMessage(msg.id)

            pass

        elif purpose == "temporary":
            messages = [
                msg
                for msg in messages
                if not (
                    isinstance(msg, AIMessage)
                    and msg.additional_kwargs.get("tag") == tag
                )
            ]

        return messages

    def reset_turn(self) -> None:
        """Reset per-turn state fields at the start of each invocation."""
        self.remove_table(self.messages, "messages")
        self.is_safe = False
        self.guardrail_message = ""
        # self.agent_answer = None
        self.intent = PlannerLabels.GNRL_CHAT
        self.selected_tool = None
        self.func_parm_schm = None
        self.db_query_list = []
        self.data_from_fkdb = "Unavailable"
        self.status = StatusLabels.PROGRESS
        # self.error_message = ""
