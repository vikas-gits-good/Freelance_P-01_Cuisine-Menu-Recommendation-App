import re
from typing import Literal

from langchain_core.messages import SystemMessage

from Src.Constants import SystemPromptConstants
from Src.Utils import LogException, log_rag, prompt_func


class SysMsgSet:
    def __init__(self):
        self.sys_pmt = self._get_prompts()

    class _get_prompts:
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
                text = prompt_func.read(path=path, chunk=False)

                pattern = r"<(\w+)_PROMPT>(.*?)</\1_PROMPT>"
                for match in re.finditer(pattern, text, re.DOTALL):  # type:ignore
                    tag_name = match.group(1).lower()
                    if tag_name.lower() == types.lower():
                        prompt = SystemMessage(content=match.group(2).strip())
                        break

            except Exception as e:
                LogException(e, logger=log_rag)
                prompt = SystemMessage(content="error getting system prompt")

            return prompt
