from enum import Enum


class GRNodeLabel(Enum):
    GUARDRAIL = "guardrail"
    MEMORY = "memory"
    PLANNER = "planner"
    EXECUTOR = "executor"
    TOOLBOX = "toolbox"
    SUMMARY = "summary"
    GENERAL = "general"
    UNSAFE = "unsafe"


class PlannerLabels(Enum):  # rename to IntentLabels
    TOOL_CALL = "tool_call"
    DABA_QERY = "daba_query"
    GNRL_CHAT = "gnrl_chat"


class StatusLabels(Enum):
    SUCCESS = "success"
    ERROR = "error"
    CLARIFY = "clarify"
    PROGRESS = "progress"


class ToolLabels(Enum):
    GET_COMPETITORS_DATA = "get_competitors_data"
    GET_COMPETITORS_MENU = "get_competitors_menu"
    GET_MENU_BENCHMARK = "get_menu_benchmark"
    GET_MENU_OPPORTUNITIES = "get_menu_opportunities"
    GET_OVERPRICED_MENU = "get_overpriced_menu"
    GET_PREMIUM_MENU = "get_premium_menu"
    GET_SPECIFIC_COMPETITOR_MENU = "get_specific_competitor_menu"
    RECOMMEND_MENU = "recommend_menu"
