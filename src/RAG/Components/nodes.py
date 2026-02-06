import json

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage

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
            messages = [
                self.sms.guardrail,
                state.user_query,
            ]
            response: GuardrailSchema = self.llm_gdrl.invoke(messages)
            gdrl_msgs = AIMessage(content=f"{response.model_dump()}")

            # update state
            state.is_safe = response.is_safe
            state.guardrail_message = response.guardrail_message
            state.conversation.append(state.user_query)
            state.conversation.append(gdrl_msgs)
            state.messages.append(state.user_query)

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
            messages = [
                SystemMessage(
                    content=self.sms.planner.content.format(
                        user_preferences=state.user_preferences,
                        user_summary=state.user_summary,
                        convo_summary=state.msg_summary,
                    ),
                ),
                *state.messages[:-1],  # conversation history
                state.user_query,  # current user query
            ]
            llm_plnr = self.llm_chat.with_structured_output(schema=PlannerOutput)
            response: PlannerOutput = llm_plnr.invoke(messages)

            # update state
            state.conversation.append(AIMessage(content=f"{response.model_dump()}"))
            state.intent = response.intent.intent
            state.selected_tool = (
                response.tool_selection.tool_name
                if response.tool_selection
                else state.selected_tool
            )
            state.status = (
                StatusLabels.CLARIFY
                if response.intent.requires_clarification
                else state.status
            )
            state.agent_answer = (
                AIMessage(content=response.intent.clarification_question)
                if response.intent.requires_clarification
                else state.agent_answer
            )

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
                messages = [
                    self.sms.executor,
                    state.user_query,
                ]
                # see if you can put another ReAct loop with a smaller model
                llm_tool = self.llm_chat.bind_tools([self.qry_parm_func])
                response = llm_tool.invoke(messages)
                state.conversation.append(response)

                args = {}
                if response.tool_calls:
                    for tc in response.tool_calls:
                        tool_result = self.qry_parm_func.invoke(tc["args"])
                        args.update({k: v[0] for k, v in tool_result.items()})

                    # construct the toolbox function parameter schema
                    state.func_parm_schm = self.tool_schm_map[
                        state.selected_tool.value
                    ](**args)

            elif state.intent == PlannerLabels.DABA_QERY:
                messages = [
                    self.sms.graphdb,  # dont use .format(max_steps=)
                    state.user_query,
                ]
                llm_tool = self.llm_chat.bind_tools([self.qry_daba_func])

                # ReAct agent loop clamped at self.max_steps
                for _ in range(self.max_steps):
                    response = llm_tool.invoke(messages)  # return cypher query
                    messages.append(response)
                    state.conversation.append(response)

                    if not response.tool_calls:
                        break

                    for tc in response.tool_calls:
                        state.db_query_list.append(
                            tc["args"].get("query", "failed to gen cypher")
                        )
                        result = self.qry_daba_func.invoke(tc["args"])
                        tool_msg = ToolMessage(
                            content=json.dumps(result),
                            tool_call_id=tc["id"],
                        )
                        messages.append(tool_msg)
                        state.conversation.append(tool_msg)

                # loop through messages and get last ToolMessage
                last_tool_msg = next(
                    (msg for msg in reversed(messages) if isinstance(msg, ToolMessage)),
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
            state.tool_result = self.tool_func_map[state.selected_tool.value].invoke(
                state.func_parm_schm.model_dump()
            )

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
            if len(state.messages) >= 6:
                messages = [self.sms.summary, state.msg_summary, *state.messages[:-4]]
                response = self.llm_chat.invoke(messages)
                state.msg_summary = AIMessage(content=response.content)
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
            messages = [
                SystemMessage(
                    content=self.sms.general.content.format(
                        convo_summary=state.msg_summary,
                        data_from_fkdb=state.data_from_fkdb,
                    )
                ),
                *state.messages[:-1],
                state.user_query,
            ]

            response = self.llm_chat.invoke(messages)
            state.conversation.append(response)
            state.messages.append(response)
            state.agent_answer = response

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
                state.conversation.append(grdm_msg)
                state.agent_answer = grdm_msg

            elif state.status == StatusLabels.CLARIFY:
                # clarification msg is already set to state.agent_answer
                state.conversation.append(state.agent_answer)

        except Exception as e:
            LogException(e, logger=log_flk)

        return state
