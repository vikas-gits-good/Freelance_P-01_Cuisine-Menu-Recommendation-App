from typing import Literal

from Src.Constants import GRNodeLabel, PlannerLabels, StatusLabels
from Src.Utils import LogException, log_rag

from .state import GRState


class GRRouter:
    """Router class containing all conditional routing functions."""

    def __init__(self):
        try:
            ...
            pass

        except Exception as e:
            LogException(e, logger=log_rag)

    def route_after_guardrail(self, state: GRState) -> Literal["memory", "unsafe"]:
        """Route based on guardrail check result."""
        decision = GRNodeLabel.UNSAFE
        try:
            if state.is_safe:
                decision = GRNodeLabel.MEMORY

        except Exception as e:
            LogException(e, logger=log_rag)

        return decision.value

    def route_after_planner(
        self, state: GRState
    ) -> Literal["executor", "unsafe", "general"]:
        """Route based on planner's intent classification."""
        decision = GRNodeLabel.GENERAL
        try:
            if state.intent in [PlannerLabels.TOOL_CALL, PlannerLabels.DABA_QERY]:
                decision = GRNodeLabel.EXECUTOR

            elif state.intent == PlannerLabels.EROR_QUIT:
                decision = GRNodeLabel.UNSAFE

            elif state.status == StatusLabels.CLARIFY:
                decision = GRNodeLabel.UNSAFE

            else:
                decision = GRNodeLabel.GENERAL

        except Exception as e:
            LogException(e, logger=log_rag)

        return decision.value

    def route_after_executor(
        self, state: GRState
    ) -> Literal["general", "unsafe", "toolbox"]:
        """Route based on executor result."""
        decision = GRNodeLabel.TOOLBOX
        try:
            if state.data_from_fkdb != "Unavailable":  # daba_query
                decision = GRNodeLabel.GENERAL

            elif state.status == StatusLabels.ERROR:  # error somewhere
                # query is not unsafe but routed to end through here
                decision = GRNodeLabel.UNSAFE

            else:  # toolbox data. Data can be empty
                decision = GRNodeLabel.TOOLBOX

        except Exception as e:
            LogException(e, logger=log_rag)

        return decision.value
