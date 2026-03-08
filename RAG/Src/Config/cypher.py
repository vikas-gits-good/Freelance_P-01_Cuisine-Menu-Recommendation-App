import re
from typing import Any, Dict, Literal

from Src.Constants import RAGCypherConstants
from Src.Utils import cypher_func


class get_cypher_code:
    def __init__(self):
        self._paths = RAGCypherConstants.ALL_CYPHER_CODE_PATH
        self.tools: Dict[str, Any] = self.get_code(code="tools")

    def get_code(self, code: Literal["tools"] = "tools"):
        path = [
            file_item for file_item in self._paths if code in file_item.split("/")[-1]
        ][0]
        cypher_list = cypher_func.read(path=path, chunk=True)
        cypher_dict = {
            match.group(1): match.group(2).strip()
            for chunk in cypher_list
            if (match := re.match(r"//\s*(\w+)\s*\n(.+)$", chunk, re.DOTALL))
        }
        return cypher_dict


class CypherCodeConfig:
    def __init__(self):
        self.cp_code = get_cypher_code()
