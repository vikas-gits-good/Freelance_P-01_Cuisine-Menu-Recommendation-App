from langgraph.graph.state import StateGraph, CompiledStateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

from src.RAG.Components.state import GRState
from src.RAG.Components.nodes import GRNodes
from src.RAG.Components.router import GRRouter
from src.RAG.Constants.labels import GRNodeLabel
from src.RAG.Constants.models import GroqModelList, OpenAIModelList

from src.Logging.logger import log_flk
from src.Exception.exception import LogException, CustomException


class LangGraphState:
    def __init__(self):
        try:
            ...
            pass

        except Exception as e:
            LogException(e, logger=log_flk)
            # raise CustomException(e)

    def build(self) -> CompiledStateGraph:
        """Method that returns the `CompiledStateGraph` object for the chat system"""
        try:
            # get nodes
            nodes = GRNodes(  # redesign this part
                chat_model=GroqModelList.meta.llama_33_70b_versatile,
                gdrl_model=GroqModelList.meta.llama_31_8b_instant,
            )
            # get routes
            router = GRRouter()

            # add nodes
            ln_graph = StateGraph(GRState)
            ln_graph.add_node(GRNodeLabel.GUARDRAIL.value, nodes.guardrail_node)
            ln_graph.add_node(GRNodeLabel.MEMORY.value, nodes.memory_node)
            ln_graph.add_node(GRNodeLabel.PLANNER.value, nodes.planner_node)
            ln_graph.add_node(GRNodeLabel.EXECUTOR.value, nodes.executor_node)
            ln_graph.add_node(GRNodeLabel.TOOLBOX.value, nodes.toolbox_node)
            ln_graph.add_node(GRNodeLabel.SUMMARY.value, nodes.summarisation_node)
            ln_graph.add_node(GRNodeLabel.GENERAL.value, nodes.genchat_node)
            ln_graph.add_node(GRNodeLabel.UNSAFE.value, nodes.unsafe_node)

            # add edges
            ln_graph.add_edge(START, GRNodeLabel.GUARDRAIL.value)
            ln_graph.add_conditional_edges(
                GRNodeLabel.GUARDRAIL.value,
                router.route_after_guardrail,
            )
            ln_graph.add_edge(GRNodeLabel.UNSAFE.value, END)
            ln_graph.add_edge(GRNodeLabel.MEMORY.value, GRNodeLabel.PLANNER.value)
            ln_graph.add_conditional_edges(
                GRNodeLabel.PLANNER.value,
                router.route_after_planner,
            )
            ln_graph.add_edge(GRNodeLabel.GENERAL.value, GRNodeLabel.SUMMARY.value)
            ln_graph.add_edge(GRNodeLabel.SUMMARY.value, END)
            ln_graph.add_conditional_edges(
                GRNodeLabel.EXECUTOR.value,
                router.route_after_executor,
            )

            # compile
            ln_state_graph = ln_graph.compile(checkpointer=InMemorySaver())

        except Exception as e:
            LogException(e, logger=log_flk)
            # raise CustomException(e)

        return ln_state_graph


# =============================================================================
# Example Usage
# =============================================================================

if __name__ == "__main__":
    from langchain_core.messages import HumanMessage

    # Create the workflow
    workflow = LangGraphState().build()

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
