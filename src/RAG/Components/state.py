from typing import Annotated, List, Literal, Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.graph.message import add_messages


class GRState(BaseModel):
    """Main state for the GraphRAG workflow."""

    # Conversation tracking
    conversation: Annotated[List[AnyMessage], add_messages] = Field(default_factory=list)
    messages: Annotated[List[HumanMessage | AIMessage], add_messages] = Field(default_factory=list)

    # Memory (mem0)
    preferences: str = Field(default="")  # user preferences from memory
    summary: str = Field(default="")  # conversation summary

    # Current turn
    user_query: Optional[HumanMessage] = None
    agent_answer: Optional[AIMessage] = None

    # Guardrails
    is_safe: bool = Field(default=True)
    guardrail_message: str = Field(default="")

    # Planner Agent outputs
    intent: Literal["tool_call", "direct_db_query", "follow_up", "general_chat"] = Field(default="general_chat")
    selected_tool: Optional[str] = None  # name of tool to call
    tool_params_raw: Dict[str, Any] = Field(default_factory=dict)  # extracted params from user query

    # Executor Agent outputs (resolved from DB)
    area_ids: Optional[str] = None
    cuisine_name: Optional[str] = None
    resolved_params: Dict[str, Any] = Field(default_factory=dict)  # final params after DB lookup

    # Tool execution
    tool_result: Dict[str, Any] = Field(default_factory=dict)
    flattened_data: str = Field(default="")  # token-optimized string representation

    # FalkorDB direct query (for small/medium queries)
    db_query: str = Field(default="")
    db_result: Dict[str, Any] = Field(default_factory=dict)

    # Flow control
    status: Literal["success", "error", "needs_clarification", "in_progress"] = Field(default="in_progress")
    error_message: str = Field(default="")
