"""
LangGraph workflow for the GraphRAG Menu Recommendation System.

Flow:
    Start → Guardrails → get_mem0 → Planner Agent
                                        ↓
                            ┌───────────┴───────────┐
                            ↓           ↓           ↓
                       tool_call   direct_db   general_chat
                            ↓           ↓           ↓
                       Executor    query_db    chat_node
                            ↓           ↓           │
                       ToolBox     flatten        │
                            ↓           │           │
                       flatten ─────────┴───────────┘
                            ↓
                       put_mem0 → check_status → End
"""

from typing import Literal

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from src.RAG.Components.state import GRState
from src.RAG.Components.nodes import GraphNodes


# =============================================================================
# Routing Functions
# =============================================================================


def route_after_guardrail(state: GRState) -> Literal["get_memory", "end_unsafe"]:
    """Route based on guardrail check result."""
    if state.is_safe:
        return "get_memory"
    return "end_unsafe"


def route_after_planner(
    state: GRState,
) -> Literal["executor", "query_db", "general_chat", "end_clarification"]:
    """Route based on planner's intent classification."""
    if state.status == "needs_clarification":
        return "end_clarification"

    intent = state.intent

    if intent == "tool_call":
        return "executor"
    elif intent == "direct_db_query":
        return "query_db"
    else:  # general_chat or follow_up
        return "general_chat"


def route_after_executor(state: GRState) -> Literal["toolbox", "error_handler"]:
    """Route based on executor result."""
    if state.status == "error":
        return "error_handler"
    return "toolbox"


# =============================================================================
# Graph Builder
# =============================================================================


def build_graph(checkpointer: bool = True) -> StateGraph:
    """
    Build the LangGraph workflow for menu recommendation.

    Args:
        checkpointer: Whether to add memory checkpointing for conversation persistence.

    Returns:
        Compiled StateGraph ready for execution.
    """
    # Initialize nodes
    nodes = GraphNodes()

    # Create the graph
    graph = StateGraph(GRState)

    # -------------------------------------------------------------------------
    # Add all nodes
    # -------------------------------------------------------------------------

    # Entry nodes
    graph.add_node("guardrail", nodes.guardrail_node)
    graph.add_node("get_memory", nodes.get_memory_node)

    # Planner Agent
    graph.add_node("planner", nodes.planner_node)

    # Executor path (tool_call intent)
    graph.add_node("executor", nodes.executor_node)
    graph.add_node("toolbox", nodes.toolbox_node)

    # Direct DB path
    graph.add_node("query_db", nodes.query_db_node)

    # General chat path
    graph.add_node("general_chat", nodes.general_chat_node)

    # Shared nodes
    graph.add_node("flatten", nodes.flatten_node)
    graph.add_node("put_memory", nodes.put_memory_node)
    graph.add_node("check_status", nodes.check_status_node)

    # Error/unsafe handlers (just pass through with appropriate response)
    graph.add_node(
        "end_unsafe",
        lambda state: {
            "agent_answer": state.guardrail_message
            or "I'm sorry, I can't help with that request.",
            "status": "error",
        },
    )
    graph.add_node(
        "error_handler",
        lambda state: {
            "status": "error",
            "flattened_data": f"Error: {state.error_message}",
        },
    )

    # -------------------------------------------------------------------------
    # Add edges
    # -------------------------------------------------------------------------

    # Start → Guardrail
    graph.add_edge(START, "guardrail")

    # Guardrail → conditional
    graph.add_conditional_edges(
        "guardrail",
        route_after_guardrail,
        {
            "get_memory": "get_memory",
            "end_unsafe": "end_unsafe",
        },
    )

    # Unsafe → End
    graph.add_edge("end_unsafe", END)

    # Get Memory → Planner
    graph.add_edge("get_memory", "planner")

    # Planner → conditional routing
    graph.add_conditional_edges(
        "planner",
        route_after_planner,
        {
            "executor": "executor",
            "query_db": "query_db",
            "general_chat": "general_chat",
            "end_clarification": "put_memory",  # Still save to memory even on clarification
        },
    )

    # Executor → conditional
    graph.add_conditional_edges(
        "executor",
        route_after_executor,
        {
            "toolbox": "toolbox",
            "error_handler": "error_handler",
        },
    )

    # ToolBox → Flatten
    graph.add_edge("toolbox", "flatten")

    # Query DB → Flatten
    graph.add_edge("query_db", "flatten")

    # General Chat → Put Memory (skip flatten since no data)
    graph.add_edge("general_chat", "put_memory")

    # Flatten → Put Memory
    graph.add_edge("flatten", "put_memory")

    # Error Handler → Put Memory
    graph.add_edge("error_handler", "put_memory")

    # Put Memory → Check Status
    graph.add_edge("put_memory", "check_status")

    # Check Status → End
    graph.add_edge("check_status", END)

    # -------------------------------------------------------------------------
    # Compile with optional checkpointer
    # -------------------------------------------------------------------------

    if checkpointer:
        memory = MemorySaver()
        compiled = graph.compile(checkpointer=memory)
    else:
        compiled = graph.compile()

    return compiled


# =============================================================================
# Convenience Functions
# =============================================================================


def create_workflow():
    """Create and return the compiled workflow with checkpointing enabled."""
    return build_graph(checkpointer=True)


def create_workflow_no_memory():
    """Create and return the compiled workflow without checkpointing."""
    return build_graph(checkpointer=False)


# =============================================================================
# Example Usage
# =============================================================================

if __name__ == "__main__":
    from langchain_core.messages import HumanMessage

    # Create the workflow
    workflow = create_workflow()

    # Example invocation
    initial_state = GRState(
        user_query=HumanMessage(
            content="Show me Thai restaurants in Indiranagar, Bangalore with good ratings"
        )
    )

    # Run with thread_id for conversation persistence
    config = {"configurable": {"thread_id": "user-123"}}

    result = workflow.invoke(initial_state.model_dump(), config)

    print("Agent Response:", result.get("agent_answer"))
    print("Status:", result.get("status"))
