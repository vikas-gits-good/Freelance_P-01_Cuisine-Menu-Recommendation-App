import re
from typing import Literal, Dict, Any
from src.Utils.main_utils import read_cypher
from src.RAG.Constants import RAGCypherConstants

from src.RAG.Config.tool_models import (
    IntentClassification,
    ToolSelection,
    ExtractedParams,
    PlannerOutput,
    ResolvedToolParams,
    CypherQueryPlan,
)


class get_cypher_code:
    def __init__(self):
        self.all_cyp_paths = RAGCypherConstants.ALL_CYPHER_CODE_PATH
        self.tools: Dict[str, Any] = self.get_code(code="tools")
        self.gdb: Dict[str, Any] = self.get_code(code="gdb")

    def get_code(self, code: Literal["tools", "gdb"] = "tools"):
        path = [
            file_item
            for file_item in self.all_cyp_paths
            if code in file_item.split("/")[-1]
        ][0]
        cypher_list = read_cypher(save_path=path, chunk=True)
        cypher_dict = {
            match.group(1): match.group(2).strip()
            for chunk in cypher_list
            if (match := re.match(r"//\s*(\w+)\s*\n(.+)$", chunk, re.DOTALL))
        }
        return cypher_dict


class CypherCodeConfig:
    def __init__(self):
        self.cp_code = get_cypher_code()


__all__ = [
    "get_cypher_code",
    "CypherCodeConfig",
    "IntentClassification",
    "ToolSelection",
    "ExtractedParams",
    "PlannerOutput",
    "ResolvedToolParams",
    "CypherQueryPlan",
]
