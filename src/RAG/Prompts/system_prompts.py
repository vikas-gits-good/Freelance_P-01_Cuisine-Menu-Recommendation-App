import re
from typing import Literal
from langchain_core.messages import SystemMessage

from src.Utils.main_utils import read_text
from src.RAG.Constants import SystemPromptConstants

from src.Logging.logger import log_flk
from src.Exception.exception import LogException


class get_prompts:
    def __init__(self):
        self._sys_pmt_path = SystemPromptConstants.SYSTEM_PROMPTS_TEXT_PATH
        self.guardrail = self._get(types="guardrail")
        self.planner = self._get(types="planner")
        self.executor = self._get(types="executor")
        self.graphdb = self._get(types="graphdb")
        self.summary = self._get(types="summary")
        self.general = self._get(types="general")

    def _get(
        self,
        types: Literal[
            "guardrail",
            "planner",
            "executor",
            "graphdb",
            "summary",
            "general",
        ] = "guardrail",
    ):
        try:
            path = self._sys_pmt_path[0]
            text = read_text(save_path=path, chunk=False)

            pattern = r"<(\w+)_PROMPT>(.*?)</\1_PROMPT>"
            for match in re.finditer(pattern, text, re.DOTALL):
                tag_name = match.group(1).lower()
                if tag_name.lower() == types.lower():
                    prompt = SystemMessage(content=match.group(2).strip())
                    break

        except Exception as e:
            LogException(e, logger=log_flk)
            prompt = SystemMessage(content="error getting system prompt")

        return prompt


class SysMsgSet:
    def __init__(self):
        self.sys_pmt = get_prompts()
