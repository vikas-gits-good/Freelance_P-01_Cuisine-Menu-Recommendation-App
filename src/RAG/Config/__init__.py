import re
from typing import Literal
from src.Utils.main_utils import read_cypher
from src.RAG.Constants import FalkorDBConstants, CypherConstants


class SwiggyFKDBConfig:
    def __init__(self):
        self.cnct_url = FalkorDBConstants.FALKORDB_CONNECTION_URI

        username, password, host, port = re.search(
            r"redis://([^:]+):([^@]+)@([^:]+):(\d+)", self.cnct_url
        ).groups()

        self.cnct_dict = {
            "username": username,
            "password": password,
            "host": host,
            "port": int(port),
        }


class FalkorDBConfig:
    def __init__(self):
        self.swiggy = SwiggyFKDBConfig()


class get_cypher_code:
    def __init__(self):
        self.all_cyp_paths = CypherConstants.ALL_CYPHER_FILE_PATHS
        self.create = self.get_code(code="create")
        self.load = self.get_code(code="load")
        self.validate = self.get_code(code="validate")

    def get_code(self, code: Literal["create", "load", "validate"] = "create"):
        path = [
            file_item
            for file_item in self.all_cyp_paths
            if code in file_item.split("/")[-1]
        ][0]
        return read_cypher(save_path=path, chunk=True)


class CypherCodeConfig:
    def __init__(self):
        self.cp_code = get_cypher_code()
