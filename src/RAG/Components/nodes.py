import json
from typing import Dict, Any, Literal

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_groq import ChatGroq

from src.RAG.Components.state import GRState
from src.RAG.Components.tools import CypherFunctionTool
from src.RAG.Config.tool_models import (
    PlannerOutput,
    IntentClassification,
    ToolSelection,
    ExtractedParams,
    ResolvedToolParams,
    CypherQueryPlan,
)
from src.RAG.Constants.models import GroqModelList

from src.Logging.logger import log_flk
from src.Exception.exception import LogException


# =============================================================================
# System Prompts
# =============================================================================

GUARDRAIL_PROMPT = """You are a guardrail for a restaurant menu analysis chatbot.
Analyze the user message and determine if it is:
1. Safe and relevant to restaurant/menu/cuisine analysis
2. Contains harmful, inappropriate, or completely off-topic content

Respond with JSON: {"is_safe": true/false, "reason": "brief explanation"}
"""

PLANNER_PROMPT = """You are the Planner Agent for a restaurant menu recommendation system.
Your job is to:
1. Classify the user's intent
2. Decide which tool to use (if any)
3. Extract relevant parameters from the query

Available tools and their purposes:
- get_competitors_data: Get basic data about competitor restaurants in an area/cuisine
- get_competitors_menu: Get menu items from competitors in an area/cuisine
- get_menu_benchmark: Compare a specific dish across competitors
- get_menu_opportunities: Find high-rated items with few competitors serving them
- get_overpriced_menu: Find overpriced menu items in an area
- get_premium_menu: Find high-priced items with proven demand
- get_specific_competitor_menu: Get full menu of a specific restaurant
- recommend_menu: Get recommended menu items above a rating threshold

Intent types:
- tool_call: User wants data that requires calling a specific tool
- direct_db_query: User wants graph schema info or simple lookups
- follow_up: User is asking a follow-up question about previous results
- general_chat: General conversation not requiring data retrieval

User preferences from memory: {preferences}
Conversation summary: {summary}
"""

EXECUTOR_PROMPT = """You are the Executor Agent for a restaurant menu recommendation system.
Your job is to:
1. Understand the user's query in context
2. Resolve parameter values by querying the database for exact matches
3. Prepare the final parameters for tool execution

The Planner has selected tool: {selected_tool}
Extracted parameters: {extracted_params}

Available areas in database (sample): {available_areas}
Available cuisines in database (sample): {available_cuisines}

You must resolve:
- city_name + area_name → area_ids (using _get_area_cuisine_from_db)
- cuisine_name → exact cuisine name from DB (using _get_area_cuisine_from_db)
"""


# =============================================================================
# Node Functions
# =============================================================================


class GraphNodes:
    """All node functions for the LangGraph workflow."""

    def __init__(
        self,
        model_name: str = GroqModelList.meta.llama_33_70b_versatile,
        guardrail_model: str = GroqModelList.meta.llama_guard_4_12b,
    ):
        self.llm = ChatGroq(model=model_name, temperature=0)
        self.guardrail_llm = ChatGroq(model=guardrail_model, temperature=0)
        self.cypher_tool = CypherFunctionTool()

        # Map tool names to methods
        self.tool_map = {
            "get_competitors_data": self.cypher_tool.get_competitors_data,
            "get_competitors_menu": self.cypher_tool.get_competitors_menu,
            "get_menu_benchmark": self.cypher_tool.get_menu_benchmark,
            "get_menu_opportunities": self.cypher_tool.get_menu_opportunities,
            "get_overpriced_menu": self.cypher_tool.get_overpriced_menu,
            "get_premium_menu": self.cypher_tool.get_premium_menu,
            "get_specific_competitor_menu": self.cypher_tool.get_specific_competitor_menu,
            "recommend_menu": self.cypher_tool.recommend_menu,
        }

    # -------------------------------------------------------------------------
    # Guardrails Node
    # -------------------------------------------------------------------------
    def guardrail_node(self, state: GRState) -> Dict[str, Any]:
        """Check if user query is safe and on-topic."""
        try:
            messages = [
                SystemMessage(content=GUARDRAIL_PROMPT),
                HumanMessage(content=state.user_query.content if state.user_query else ""),
            ]
            response = self.guardrail_llm.invoke(messages)

            # Parse response
            result = json.loads(response.content)
            is_safe = result.get("is_safe", True)
            reason = result.get("reason", "")

            return {
                "is_safe": is_safe,
                "guardrail_message": reason if not is_safe else "",
            }

        except Exception as e:
            LogException(e, logger=log_flk)
            # Default to safe on parse error
            return {"is_safe": True, "guardrail_message": ""}

    # -------------------------------------------------------------------------
    # Get Memory Node (mem0)
    # -------------------------------------------------------------------------
    def get_memory_node(self, state: GRState) -> Dict[str, Any]:
        """Retrieve user preferences and conversation summary from mem0."""
        try:
            # TODO: Integrate with mem0 client
            # For now, return existing state values
            return {
                "preferences": state.preferences or "No preferences stored yet.",
                "summary": state.summary or "New conversation.",
            }
        except Exception as e:
            LogException(e, logger=log_flk)
            return {"preferences": "", "summary": ""}

    # -------------------------------------------------------------------------
    # Planner Agent Node
    # -------------------------------------------------------------------------
    def planner_node(self, state: GRState) -> Dict[str, Any]:
        """Classify intent, select tool, and extract parameters."""
        try:
            prompt = PLANNER_PROMPT.format(
                preferences=state.preferences,
                summary=state.summary,
            )

            # Use structured output
            structured_llm = self.llm.with_structured_output(PlannerOutput)

            messages = [
                SystemMessage(content=prompt),
                *state.messages[-5:],  # Last 5 messages for context
                HumanMessage(content=state.user_query.content if state.user_query else ""),
            ]

            result: PlannerOutput = structured_llm.invoke(messages)

            # Build output dict
            output = {
                "intent": result.intent.intent,
                "tool_params_raw": result.extracted_params.model_dump(),
            }

            if result.tool_selection:
                output["selected_tool"] = result.tool_selection.tool_name

            if result.intent.requires_clarification:
                output["status"] = "needs_clarification"
                output["agent_answer"] = AIMessage(
                    content=result.intent.clarification_question or "Could you please provide more details?"
                )

            return output

        except Exception as e:
            LogException(e, logger=log_flk)
            return {
                "intent": "general_chat",
                "status": "error",
                "error_message": str(e),
            }

    # -------------------------------------------------------------------------
    # Executor Agent Node
    # -------------------------------------------------------------------------
    def executor_node(self, state: GRState) -> Dict[str, Any]:
        """Resolve parameters from DB and prepare for tool execution."""
        try:
            raw_params = state.tool_params_raw
            resolved = {}

            # Resolve area_ids if city/area provided
            if raw_params.get("city_name") or raw_params.get("area_name"):
                area_ids = self.cypher_tool._get_area_cuisine_from_db(
                    city_name=raw_params.get("city_name"),
                    area_name=raw_params.get("area_name"),
                    cuis_name=None,
                    purpose="get_area_ids",
                )
                resolved["area_ids"] = area_ids

            # Resolve cuisine name if provided
            if raw_params.get("cuisine_name"):
                cuisine = self.cypher_tool._get_area_cuisine_from_db(
                    city_name=None,
                    area_name=None,
                    cuis_name=raw_params.get("cuisine_name"),
                    purpose="get_cuisine_name",
                )
                resolved["cuisine"] = cuisine

            # Copy other params
            if raw_params.get("menu_name"):
                resolved["menu_name"] = raw_params["menu_name"]
            if raw_params.get("min_rating"):
                resolved["min_rating"] = raw_params["min_rating"]
                resolved["min_menu_rating"] = raw_params["min_rating"]
                resolved["min_avg_rating"] = raw_params["min_rating"]
            if raw_params.get("limit"):
                resolved["limit"] = raw_params["limit"]

            return {
                "area_ids": resolved.get("area_ids"),
                "cuisine_name": resolved.get("cuisine"),
                "resolved_params": resolved,
            }

        except Exception as e:
            LogException(e, logger=log_flk)
            return {
                "status": "error",
                "error_message": f"Failed to resolve parameters: {e}",
            }

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
    # Flatten Data Node
    # -------------------------------------------------------------------------
    def flatten_node(self, state: GRState) -> Dict[str, Any]:
        """Convert tool result to token-optimized string format."""
        try:
            data = state.tool_result or state.db_result

            if not data:
                return {"flattened_data": "No data retrieved."}

            # Convert dict to condensed string representation
            lines = []
            if isinstance(data, dict):
                # Get column names
                columns = list(data.keys())
                if columns and data[columns[0]]:
                    num_rows = len(data[columns[0]])

                    # Header
                    lines.append(" | ".join(columns))
                    lines.append("-" * 50)

                    # Rows (limit to first 20 for token efficiency)
                    for i in range(min(num_rows, 20)):
                        row_values = [str(data[col][i])[:50] for col in columns]
                        lines.append(" | ".join(row_values))

                    if num_rows > 20:
                        lines.append(f"... and {num_rows - 20} more rows")

            flattened = "\n".join(lines)
            return {"flattened_data": flattened}

        except Exception as e:
            LogException(e, logger=log_flk)
            return {"flattened_data": f"Error flattening data: {e}"}

    # -------------------------------------------------------------------------
    # Query FalkorDB Node (for direct queries)
    # -------------------------------------------------------------------------
    def query_db_node(self, state: GRState) -> Dict[str, Any]:
        """Execute a direct Cypher query against FalkorDB."""
        try:
            if not state.db_query:
                return {"db_result": {}}

            result = self.cypher_tool._query_falkordb(query=state.db_query)
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

User question: {state.user_query.content if state.user_query else ''}

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
                "agent_answer": AIMessage(content="I couldn't retrieve the requested data."),
                "status": "error",
            }

        except Exception as e:
            LogException(e, logger=log_flk)
            return {
                "agent_answer": AIMessage(content="An error occurred generating the response."),
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
