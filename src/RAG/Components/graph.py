import time
import uuid
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.state import StateGraph, CompiledStateGraph, START, END

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
            self.graph = None

        except Exception as e:
            LogException(e, logger=log_flk)
            # raise CustomException(e)

    def build(self) -> CompiledStateGraph:
        """Method that returns the `CompiledStateGraph` object for the chat system"""
        try:
            log_flk.info("GRAG: Starting to build graph rag")
            nodes = GRNodes(  # redesign this part
                chat_model=GroqModelList.meta.llama_33_70b_versatile,
                gdrl_model=GroqModelList.meta.llama_31_8b_instant,
            )
            log_flk.info("GRAG: Preparing routes for GRAG")
            router = GRRouter()

            log_flk.info("GRAG: Preparing nodes for GRAG")
            ln_graph = StateGraph(GRState)
            ln_graph.add_node(GRNodeLabel.GUARDRAIL.value, nodes.guardrail_node)
            ln_graph.add_node(GRNodeLabel.MEMORY.value, nodes.memory_node)
            ln_graph.add_node(GRNodeLabel.PLANNER.value, nodes.planner_node)
            ln_graph.add_node(GRNodeLabel.EXECUTOR.value, nodes.executor_node)
            ln_graph.add_node(GRNodeLabel.TOOLBOX.value, nodes.toolbox_node)
            ln_graph.add_node(GRNodeLabel.SUMMARY.value, nodes.summarisation_node)
            ln_graph.add_node(GRNodeLabel.GENERAL.value, nodes.genchat_node)
            ln_graph.add_node(GRNodeLabel.UNSAFE.value, nodes.unsafe_node)

            log_flk.info("GRAG: Preparing edges for GRAG")
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

            log_flk.info("GRAG: Compiling graph rag")
            self.graph = ln_graph.compile()  # checkpointer=InMemorySaver())

        except Exception as e:
            LogException(e, logger=log_flk)
            # raise CustomException(e)

        return self.graph

    def run(self, question: str, user_id: str) -> dict:
        try:
            _ = self.build() if not self.graph else None

            log_flk.info("GRAG: Preparing user query")
            epoch = int(time.time())
            sesn_id = str(uuid.uuid4())
            init_state = GRState(
                messages=[HumanMessage(content=question)],
                user_id=user_id,
                session_id=sesn_id,
            )
            config = {
                "configurable": {
                    "thread_id": f"user_{user_id}_time_{epoch}_sesn_{sesn_id}"
                }
            }

            log_flk.info("GRAG: Sending query to GRAG system")
            response = self.graph.invoke(init_state, config)

        except Exception as e:
            LogException(e, logger=log_flk)
            # raise CustomException(e)

        return response
