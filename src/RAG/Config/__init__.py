import re
from typing import Literal
from src.Utils.main_utils import read_cypher, read_json
from src.RAG.Constants import RAGCypherConstants


class get_cypher_code:
    def __init__(self):
        self.all_cyp_paths = RAGCypherConstants.ALL_CYPHER_CODE_PATH
        self.tools = self.get_code(code="tools")

    def get_code(self, code: Literal["tools"] = "tools"):
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


class get_cypher_cols:
    def __init__(self):
        self.cols: dict = read_json(RAGCypherConstants.ALL_CYPHER_COLS_PATH[0])


class CypherCodeConfig:
    def __init__(self):
        self.cp_code = get_cypher_code()
        self.cp_cols = get_cypher_cols()
