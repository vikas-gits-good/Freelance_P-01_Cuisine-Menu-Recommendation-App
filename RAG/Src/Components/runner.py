import asyncio

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from Src.Constants import StatusLabels
from Src.Utils import LogException, log_rag

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
        try:
            config = {"configurable": {"thread_id": thread_id}}
            input_state = {"messages": [HumanMessage(content=message)]}
            result = await asyncio.to_thread(self.graph.invoke, input_state, config)
            if result.get("status") == StatusLabels.ERROR:
                result = {
                    "messages": [
                        AIMessage(
                            content=result.get(
                                "error_message", "Unknown error in system"
                            )
                        )
                    ]
                }
                log_rag.info(f"{result = }")  # keep this

        except Exception as e:
            LogException(e, logger=log_rag)
            result = {"messages": [AIMessage(content="Unknown error in system")]}

        return result


runner = GraphRunner()


# result = {
#     "messages": [
#         HumanMessage(
#             content="Who are my competitors in rajajinagar, Bangalore who serve thai cuisine",
#             additional_kwargs={},
#             response_metadata={},
#             id="1d8dddf1-4b62-496d-bded-1629f7a2cb4d",
#         )
#     ],
#     "debug_convo": [
#         HumanMessage(
#             content="Who are my competitors in rajajinagar, Bangalore who serve thai cuisine",
#             additional_kwargs={},
#             response_metadata={},
#             id="1d8dddf1-4b62-496d-bded-1629f7a2cb4d",
#         ),
#         AIMessage(
#             content="{'is_safe': True, 'guardrail_message': 'Your query is safe and relevant to restaurant/menu/cuisine analysis. I can help you find competitors in Rajajinagar, Bangalore serving Thai cuisine.'}",
#             additional_kwargs={},
#             response_metadata={},
#             id="7b32315f-ef1d-4891-8aff-7b5d164fd7dc",
#             tool_calls=[],
#             invalid_tool_calls=[],
#         ),
#     ],
#     "msg_summary": AIMessage(
#         content="Unavailable",
#         additional_kwargs={},
#         response_metadata={},
#         tool_calls=[],
#         invalid_tool_calls=[],
#     ),
#     "is_safe": True,
#     "guardrail_message": "Your query is safe and relevant to restaurant/menu/cuisine analysis. I can help you find competitors in Rajajinagar, Bangalore serving Thai cuisine.",
#     "user_id": "Unavailable",
#     "session_id": "",
#     "turn_count": 0,
#     "user_preferences": "Unavailable",
#     "user_summary": "Unavailable",
#     "intent": "eror_quit",
#     "selected_tool": None,
#     "func_parm_schm": None,
#     "db_query_list": [],
#     "data_from_fkdb": "Unavailable",
#     "status": "progress",
# }
