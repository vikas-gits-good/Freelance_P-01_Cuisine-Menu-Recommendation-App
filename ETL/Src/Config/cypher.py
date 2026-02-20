import re
from typing import Literal

from Src.Constants import ETLCyphersConstants
from Src.Utils import cypher_func


class _get_cypher_code:
    def __init__(self):
        self.all_cyp_paths = ETLCyphersConstants.ALL_CYPHER_FILE_PATHS
        self.create = self._get_code(code="create")
        self.upsert = self._get_code(code="upsert")
        self.validate = self._get_code(code="validate")

    def _get_code(self, code: Literal["create", "upsert", "validate"] = "create"):
        path = [
            file_item
            for file_item in self.all_cyp_paths
            if code in file_item.split("/")[-1]
        ][0]
        cypher_list = cypher_func.read(path=path, chunk=True)
        cypher_dict = {
            match.group(1): match.group(2).strip()
            for chunk in cypher_list
            if (match := re.match(r"//\s*(\w+)\s*\n(.+)$", chunk, re.DOTALL))
        }
        return cypher_dict


class ETLCypherConfig:
    """Method to get cypher code for ETL-loader operations"""

    def __init__(self):
        self.cp_code = _get_cypher_code()
