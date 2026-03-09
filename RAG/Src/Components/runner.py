import asyncio

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from .graph import LangGraphState


class GraphRunner:
    """Singleton that holds one compiled graph, shared across all requests."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def initialize(self):
        if self._initialized:
            return
        checkpointer = InMemorySaver()
        state = LangGraphState()
        self.graph = state.build(checkpointer=checkpointer)
        self._initialized = True

    async def invoke(self, message: str, thread_id: str) -> dict:
        """Run graph in thread pool to avoid blocking the event loop."""
        config = {"configurable": {"thread_id": thread_id}}
        input_state = {"messages": [HumanMessage(content=message)]}

        result = await asyncio.to_thread(self.graph.invoke, input_state, config)
        return result


runner = GraphRunner()
