import os

from dotenv import load_dotenv
from langgraph.graph.state import END, START, CompiledStateGraph, StateGraph

from Src.Constants import GRNodeLabel, Models
from Src.Utils import LogException, log_rag

from .nodes import GRNodes
from .router import GRRouter
from .state import GRState


class LangGraphState:
    def __init__(self):
        try:
            self.graph = None
            load_dotenv()
            self.large = os.getenv(
                "MODEL_LARGE",
                Models.Groq.meta.llama_33_70b_versatile,
            )
            self.small = os.getenv(
                "MODEL_SMALL",
                Models.Groq.meta.llama_31_8b_instant,
            )

        except Exception as e:
            LogException(e, logger=log_rag)

    def build(self, checkpointer) -> CompiledStateGraph:
        """Method that returns the `CompiledStateGraph` object for the chat system"""
        try:
            log_rag.info("GRAG: Starting to build graph rag")
            nodes = GRNodes(  # redesign this part
                large_model=self.large,
                small_model=self.small,
            )
            log_rag.info("GRAG: Preparing routes for GRAG")
            router = GRRouter()

            log_rag.info("GRAG: Preparing nodes for GRAG")
            ln_graph = StateGraph(GRState)
            ln_graph.add_node(GRNodeLabel.GUARDRAIL.value, nodes.guardrail_node)
            ln_graph.add_node(GRNodeLabel.MEMORY.value, nodes.memory_node)
            ln_graph.add_node(GRNodeLabel.PLANNER.value, nodes.planner_node)
            ln_graph.add_node(GRNodeLabel.EXECUTOR.value, nodes.executor_node)
            ln_graph.add_node(GRNodeLabel.TOOLBOX.value, nodes.toolbox_node)
            ln_graph.add_node(GRNodeLabel.SUMMARY.value, nodes.summarisation_node)
            ln_graph.add_node(GRNodeLabel.GENERAL.value, nodes.genchat_node)
            ln_graph.add_node(GRNodeLabel.UNSAFE.value, nodes.unsafe_node)

            log_rag.info("GRAG: Preparing edges for GRAG")
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
            ln_graph.add_edge(GRNodeLabel.TOOLBOX.value, GRNodeLabel.SUMMARY.value)

            log_rag.info("GRAG: Compiling graph rag")
            self.graph = ln_graph.compile(checkpointer)

        except Exception as e:
            LogException(e, logger=log_rag)

        return self.graph
