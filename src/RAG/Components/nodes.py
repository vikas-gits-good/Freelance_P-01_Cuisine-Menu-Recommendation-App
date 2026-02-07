import json
import pandas as pd
from typing import Union, Any, Dict

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage, HumanMessage

from src.RAG.Components.state import GRState
from src.RAG.Components.tools import GRTools
from src.RAG.Prompts.system_prompts import SysMsgSet
from src.RAG.Config.tool_models import (
    GuardrailSchema,
    UserPreferenceSchema,
    PlannerOutput,
)
from src.RAG.Config.models import ModelConfig
from src.RAG.Constants.models import GroqModelList
from src.RAG.Constants.labels import StatusLabels, PlannerLabels

from src.Logging.logger import log_flk
from src.Exception.exception import LogException


class GRNodes:
    """All node functions for the LangGraph workflow."""

    def __init__(
        self,
        chat_model: str = GroqModelList.meta.llama_33_70b_versatile,
        gdrl_model: str = GroqModelList.meta.llama_31_8b_instant,
        mdl_config: ModelConfig = ModelConfig(),
    ):
        try:
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
            self.dqt = GRTools()
            self.tool_func_map = self.dqt.db_tool_box_func
            self.tool_schm_map = self.dqt.db_tool_box_schm
            self.qry_parm_func = self.dqt._get_params_from_db
            self.qry_daba_func = self.dqt._query_falkordb
            self.max_steps: int = 6

        except Exception as e:
            LogException(e, logger=log_flk)

    # -------------------------------------------------------------------------
    # Guardrail Node -> No suspicious queries goes through
    # -------------------------------------------------------------------------
    def guardrail_node(self, state: GRState) -> GRState:
        """Check if user query is safe and on-topic."""
        try:
            state.reset_turn()  # reset prev state
            convo = [
                self.sms.guardrail,  # system prompt - guardrail
                state.messages[-1],  # user query - latest
            ]
            response: GuardrailSchema = self.llm_gdrl.invoke(convo)
            gdrl_msgs = AIMessage(content=f"{response.model_dump()}")

            # update state
            state.is_safe = response.is_safe
            state.guardrail_message = response.guardrail_message
            state.debug_convo.append(state.messages[-1])  # add user query
            state.debug_convo.append(gdrl_msgs)  # add grdl response

        except Exception as e:
            LogException(e, logger=log_flk)

        return state

    # -------------------------------------------------------------------------
    # User Memory Node -> Get user's data from memory ## Not Implemented
    # -------------------------------------------------------------------------
    def memory_node(self, state: GRState) -> GRState:
        """Retrieve user preferences and conversation summary from mem0."""
        try:
            # TODO: Integrate with mem0 client
            pass
            data: UserPreferenceSchema = UserPreferenceSchema()

            # update state
            state.user_preferences = data.user_preferences
            state.user_summary = data.user_summary

        except Exception as e:
            LogException(e, logger=log_flk)

        return state

    # -------------------------------------------------------------------------
    # Planner Agent Node -> decide how to best address user query
    # -------------------------------------------------------------------------
    def planner_node(self, state: GRState) -> GRState:
        """Classify intent, select tool, and extract parameters."""
        try:
            convo = [
                SystemMessage(  # system prompt - planner
                    content=self.sms.planner.content.format(
                        user_preferences=state.user_preferences,
                        user_summary=state.user_summary,
                        convo_summary=state.msg_summary,
                    ),
                ),
                *state.messages,  # user query - full conversation
            ]
            llm_plnr = self.llm_chat.with_structured_output(schema=PlannerOutput)
            response: PlannerOutput = llm_plnr.invoke(convo)

            # update state
            state.debug_convo.append(AIMessage(content=f"{response.model_dump()}"))
            state.intent = response.intent.intent
            if response.tool_selection:
                state.selected_tool = response.tool_selection.tool_name

            if response.intent.requires_clarification:
                clrf_qstn = AIMessage(content=response.intent.clarification_question)
                state.agent_answer = clrf_qstn
                state.status = StatusLabels.CLARIFY
                state.debug_convo.append(clrf_qstn)
                state.messages.append(clrf_qstn)

        except Exception as e:
            LogException(e, logger=log_flk)

        return state

    # -------------------------------------------------------------------------
    # Executor Agent Node
    # -------------------------------------------------------------------------
    def executor_node(self, state: GRState) -> GRState:
        """Execute plan to either call toolbox function or directly query db"""
        try:
            if state.intent == PlannerLabels.TOOL_CALL:
                convo = [
                    self.sms.executor,  # system prompt - executor
                    state.messages[-1],  # user query - latest
                ]
                # see if you can put another ReAct loop with a smaller model
                llm_tool = self.llm_chat.bind_tools([self.qry_parm_func])
                response = llm_tool.invoke(convo)
                state.debug_convo.append(response)

                args = {}
                if response.tool_calls:
                    for tc in response.tool_calls:
                        tool_result = self.qry_parm_func.invoke(tc["args"])
                        args.update({k: v[0] for k, v in tool_result.items()})

                    # construct the toolbox function parameter schema
                    state.func_parm_schm = self.tool_schm_map[
                        state.selected_tool.value
                    ](**args)

                state.debug_convo.append(
                    ToolMessage(content=f"{args}", tool_call_id="placeholder_id")
                )

            elif state.intent == PlannerLabels.DABA_QERY:
                convo = [
                    self.sms.graphdb,  # system prompt - graphdb
                    state.messages[-1],  # user query - latest
                ]
                llm_tool = self.llm_chat.bind_tools([self.qry_daba_func])

                # ReAct agent loop clamped at self.max_steps
                for _ in range(self.max_steps):
                    response = llm_tool.invoke(convo)  # returns cypher query
                    convo.append(response)
                    state.debug_convo.append(response)

                    if not response.tool_calls:
                        break

                    for tc in response.tool_calls:
                        state.db_query_list.append(
                            tc["args"].get("query", "failed to gen cypher")
                        )
                        result = self.qry_daba_func.invoke(tc["args"])
                        tool_msg = ToolMessage(
                            content=json.dumps(result),  # json string
                            tool_call_id=tc["id"],
                        )
                        convo.append(tool_msg)
                        state.debug_convo.append(tool_msg)

                # loop through local convo and get last ToolMessage
                last_tool_msg = next(
                    (msg for msg in reversed(convo) if isinstance(msg, ToolMessage)),
                    None,
                )
                state.data_from_fkdb = last_tool_msg.content if last_tool_msg else None

        except Exception as e:
            LogException(e, logger=log_flk)

        return state

    # -------------------------------------------------------------------------
    # ToolBox Node
    # -------------------------------------------------------------------------
    def toolbox_node(self, state: GRState) -> GRState:
        """Execute the selected tool with resolved parameters."""
        try:
            data = self.tool_func_map[state.selected_tool.value].invoke(
                {"param_model": state.func_parm_schm}
            )

            # convert data into markdown for display in LangSmith Studio
            data_md = GRNodes.to_markdown(data)
            data_msg = AIMessage(
                content=data_md,
                tool_call_id=f"{PlannerLabels.TOOL_CALL.value}_data",
            )
            state.messages.append(data_msg)
            state.debug_convo.append(data_msg)

        except Exception as e:
            LogException(e, logger=log_flk)

        return state

    # -------------------------------------------------------------------------
    # Summarisation Node
    # -------------------------------------------------------------------------
    def summarisation_node(self, state: GRState) -> GRState:
        """Save conversation updates to mem0."""
        try:
            # TODO: Integrate with mem0 client
            pass

            # summarisation
            # remove tabular data if present
            temp_convo = [
                msg
                for msg in state.messages
                if not (
                    isinstance(msg, AIMessage)
                    and getattr(msg, "tool_call_id", None)
                    == f"{PlannerLabels.TOOL_CALL.value}_data"
                )
            ]
            if len(state.messages) >= 6:
                convo = [
                    SystemMessage(  # system prompt - summary
                        content=self.sms.summary.content.format(
                            prev_summary=state.msg_summary,
                        )  # conversation summary - previous
                    ),
                    *temp_convo[:-4],
                ]
                state.msg_summary = self.llm_chat.invoke(convo).content
                state.messages = state.messages[:-4]

        except Exception as e:
            LogException(e, logger=log_flk)

        return state

    # -------------------------------------------------------------------------
    # General Chat Node
    # -------------------------------------------------------------------------
    def genchat_node(self, state: GRState) -> GRState:
        """Handle general conversation without tool calls."""
        try:
            convo = [  # system prompt - general
                SystemMessage(
                    content=self.sms.general.content.format(
                        convo_summary=state.msg_summary,
                        data_from_fkdb=state.data_from_fkdb,
                    )
                ),
                *state.messages,  # conversation data - full
            ]

            response = self.llm_chat.invoke(convo)
            state.debug_convo.append(response)
            state.messages.append(response)

        except Exception as e:
            LogException(e, logger=log_flk)

        return state

    # -------------------------------------------------------------------------
    # Unsafe Node - Handle unsafe query, clarification and errors
    # -------------------------------------------------------------------------
    def unsafe_node(self, state: GRState) -> GRState:
        """Return unsafe queries."""
        try:
            if not state.is_safe:
                grdm_msg = AIMessage(content=state.guardrail_message)
                state.messages.append(grdm_msg)

        except Exception as e:
            LogException(e, logger=log_flk)

        return state

    @staticmethod
    def to_markdown(data: Union[str, Dict[str, Any], pd.DataFrame]) -> str:
        """Static method to convert data from FalkorDB into a markdown string format for visualisation
        in LangSmith Studio.

        Args:
            data (Union[str, Dict[str, Any], pd.DataFrame]): The data from FalkorDB.

        Returns:
            data (str): Tabular data in markdown format.
        """
        try:
            if isinstance(data, dict):
                data = pd.DataFrame(data)

            elif isinstance(data, str):
                data = pd.DataFrame(json.loads(data))

            elif isinstance(data, pd.DataFrame):
                data = data

            data = data.to_markdown(index=False)

        except Exception as e:
            LogException(e, logger=log_flk)

        return data
