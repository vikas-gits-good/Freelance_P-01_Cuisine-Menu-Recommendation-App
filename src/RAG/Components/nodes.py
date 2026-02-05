import json
from typing import Dict, Any, Literal

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_groq import ChatGroq

from src.RAG.Components.state import GRState
from src.RAG.Components.tools import DatabaseQueryTools
from src.RAG.Prompts.system_prompts import SysMsgSet
from src.RAG.Config.tool_models import (
    GuardrailSchema,
    PlannerOutput,
)
from src.RAG.Config.models import ModelConfig
from src.RAG.Constants.models import GroqModelList

from src.Logging.logger import log_flk
from src.Exception.exception import LogException


class GraphNodes:
    """All node functions for the LangGraph workflow."""

    def __init__(
        self,
        chat_model: str = GroqModelList.meta.llama_33_70b_versatile,
        gdrl_model: str = GroqModelList.meta.llama_31_8b_instant,
        mdl_config: ModelConfig = ModelConfig(),
    ):
        # change this to control opai vs groq models
        self.llm_chat = ChatGroq(
            model=chat_model,
            api_key=mdl_config.api_key.groq,
            temperature=0.7,
        )
        self.llm_gdrl = ChatGroq(
            model=gdrl_model,
            api_key=mdl_config.api_key.groq,
            temperature=0,
        ).with_structured_output(schema=GuardrailSchema)

        self.sms = SysMsgSet().sys_pmt
        dqt = DatabaseQueryTools()
        self.tool_func_map = dqt.db_tool_box_func
        self.tool_schm_map = dqt.db_tool_box_schm

    # -------------------------------------------------------------------------
    # Guardrail Node -> No suspicious queries goes through
    # -------------------------------------------------------------------------
    def guardrail_node(self, state: GRState) -> GRState:
        """Check if user query is safe and on-topic."""
        messages = [
            self.sms.guardrail,
            state.user_query,
        ]
        response = self.llm_gdrl.invoke(messages).model_dump()
        gdrl_msgs = AIMessage(content=f"{response}")
        state.conversation.append(gdrl_msgs)
        # state.messages.append(gdrl_msgs) # dont add
        return state.model_copy(update=response)

    # -------------------------------------------------------------------------
    # User Memory Node -> Get user's data from memory
    # -------------------------------------------------------------------------
    def memory_node(self, state: GRState) -> GRState:
        """Retrieve user preferences and conversation summary from mem0."""
        data = {
            "preferences": "Nothing stored yet.",
            "summary": "Nothing stored yet.",
        }
        return state.model_copy(update=data)

    # -------------------------------------------------------------------------
    # Planner Agent Node -> decide how to best address user query
    # -------------------------------------------------------------------------
    def planner_node(self, state: GRState) -> GRState:
        """Classify intent, select tool, and extract parameters."""
        try:
            messages = [
                SystemMessage(
                    content=self.sms.planner.content.format(
                        preferences=state.user_preferences,
                        summary=state.user_summary,
                    ),
                ),  # planner sys msg with user memory
                state.msg_summary,  # conversation summary
                *state.messages[-3:-1],  # conversation history
                state.user_query,  # current user query
            ]  # double check this
            llm_plnr = self.llm_chat.with_structured_output(schema=PlannerOutput)
            response: PlannerOutput = llm_plnr.invoke(messages)

            # Build output dict
            output = {
                "intent": response.intent.intent,
                "tool_params_raw": {},  # response.extracted_params.model_dump(), # remove this
            }

            if response.tool_selection:
                output["selected_tool"] = response.tool_selection.tool_name

            if response.intent.requires_clarification:
                output["status"] = "needs_clarification"
                output["agent_answer"] = AIMessage(
                    content=response.intent.clarification_question
                )

        except Exception as e:
            LogException(e, logger=log_flk)
            output = {}

        return state.model_copy(update=output)

    # -------------------------------------------------------------------------
    # Executor Agent Node
    # -------------------------------------------------------------------------
    def executor_node(self, state: GRState) -> GRState:
        """Resolve parameters from DB and prepare for tool execution."""
        try:
            # look at planner agent intent "tool_call", "direct_db_query"
            if state.intent == "tool_call":
                messages = [
                    self.sms.executor,
                    state.user_query,
                ]
                llm_tool = self.llm_chat.bind_tools(
                    [self.tool_func_map["_get_params_from_db"]]
                )
                response = llm_tool.invoke(messages)
                args = {}

                if response.tool_calls:
                    for tc in response.tool_calls:
                        tool_args = tc["args"]
                        tool_result = self.tool_func_map["_get_params_from_db"].invoke(
                            tool_args
                        )
                        args.update({k: v[0] for k, v in tool_result.items()})

                tool_schm = self.tool_schm_map[state.selected_tool](**args)

                state = state  # put this filled up func schema into a GRState var and return

        except Exception as e:
            LogException(e, logger=log_flk)

    # -------------------------------------------------------------------------
    # ToolBox Node
    # -------------------------------------------------------------------------
    def toolbox_node(self, state: GRState) -> Dict[str, Any]:
        """Execute the selected tool with resolved parameters."""
        try:
            tool_name = state.selected_tool
            if not tool_name or tool_name not in self.tool_map:
                return {
                    "status": "error",
                    "error_message": f"Unknown tool: {tool_name}",
                }

            tool_func = self.tool_map[tool_name]
            params = state.resolved_params

            # Build q_params based on tool requirements
            q_params = {}
            if params.get("area_ids"):
                q_params["area_ids"] = params["area_ids"]
            if params.get("cuisine"):
                q_params["cuisine"] = params["cuisine"]
            if params.get("menu_name"):
                q_params["menu_name"] = params["menu_name"]
            if params.get("rstn_id"):
                q_params["rstn_id"] = params["rstn_id"]
            if params.get("min_rating"):
                q_params["min_rating"] = params["min_rating"]
            if params.get("min_menu_rating"):
                q_params["min_menu_rating"] = params["min_menu_rating"]
            if params.get("min_listings"):
                q_params["min_listings"] = params["min_listings"]
            if params.get("min_avg_rating"):
                q_params["min_avg_rating"] = params["min_avg_rating"]
            if params.get("max_avg_rating"):
                q_params["max_avg_rating"] = params["max_avg_rating"]

            q_params["limit"] = params.get("limit", 200)

            # Execute tool
            result = tool_func(q_params=q_params, output="dict")

            return {"tool_result": result}

        except Exception as e:
            LogException(e, logger=log_flk)
            return {
                "tool_result": {},
                "status": "error",
                "error_message": f"Tool execution failed: {e}",
            }

    # -------------------------------------------------------------------------
    # Query FalkorDB Node (for direct queries)
    # -------------------------------------------------------------------------
    def query_db_node(self, state: GRState) -> Dict[str, Any]:
        """Execute a direct Cypher query against FalkorDB."""
        try:
            if not state.db_query:
                return {"db_result": {}}

            result = self.cft._query_falkordb(query=state.db_query)
            return {"db_result": result}

        except Exception as e:
            LogException(e, logger=log_flk)
            return {
                "db_result": {},
                "status": "error",
                "error_message": f"DB query failed: {e}",
            }

    # -------------------------------------------------------------------------
    # Put Memory Node (mem0)
    # -------------------------------------------------------------------------
    def put_memory_node(self, state: GRState) -> Dict[str, Any]:
        """Save conversation updates to mem0."""
        try:
            # TODO: Integrate with mem0 client
            # For now, just pass through
            return {}

        except Exception as e:
            LogException(e, logger=log_flk)
            return {}

    # -------------------------------------------------------------------------
    # Check Status Node
    # -------------------------------------------------------------------------
    def check_status_node(self, state: GRState) -> Dict[str, Any]:
        """Final status check and response generation."""
        try:
            if state.status == "error":
                return {
                    "agent_answer": AIMessage(
                        content=f"I encountered an error: {state.error_message}. Please try again."
                    ),
                    "status": "error",
                }

            # Generate final response using flattened data
            if state.flattened_data:
                response_prompt = f"""Based on the following data, provide a helpful response to the user's question.

User question: {state.user_query.content if state.user_query else ""}

Data:
{state.flattened_data}

Provide a concise, informative response summarizing the key insights from this data."""

                messages = [
                    SystemMessage(content="You are a helpful restaurant menu analyst."),
                    HumanMessage(content=response_prompt),
                ]

                response = self.llm.invoke(messages)
                return {
                    "agent_answer": AIMessage(content=response.content),
                    "status": "success",
                }

            return {
                "agent_answer": AIMessage(
                    content="I couldn't retrieve the requested data."
                ),
                "status": "error",
            }

        except Exception as e:
            LogException(e, logger=log_flk)
            return {
                "agent_answer": AIMessage(
                    content="An error occurred generating the response."
                ),
                "status": "error",
            }

    # -------------------------------------------------------------------------
    # General Chat Node (for non-tool conversations)
    # -------------------------------------------------------------------------
    def general_chat_node(self, state: GRState) -> Dict[str, Any]:
        """Handle general conversation without tool calls."""
        try:
            messages = [
                SystemMessage(
                    content="You are a helpful restaurant menu recommendation assistant. "
                    "Answer general questions about restaurants, cuisines, and menus."
                ),
                *state.messages[-5:],
                state.user_query,
            ]

            response = self.llm.invoke(messages)
            return {
                "agent_answer": AIMessage(content=response.content),
                "status": "success",
            }

        except Exception as e:
            LogException(e, logger=log_flk)
            return {
                "agent_answer": AIMessage(content="I'm sorry, I encountered an error."),
                "status": "error",
            }
