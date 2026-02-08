import os
import re
from glob import glob
from typing import Literal
from dotenv import load_dotenv
from src.Utils.main_utils import read_cypher


class get_cypher_code:
    def __init__(self):
        self.all_cyp_paths = glob("src/RAG/User/Cyphers/*.cyp")
        self.set = self.get_code(code="set")
        self.get = self.get_code(code="get")
        self.put = self.get_code(code="put")

    def get_code(self, code: Literal["set", "get", "put"] = "set"):
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


class UserCypherConfig:
    def __init__(self):
        load_dotenv("src/Secrets/Database.env")

        self.cp_code = get_cypher_code()
        self.auth_params = {
            "username": str(os.getenv("FALKORDB_USERNAME")),
            "password": str(os.getenv("FALKORDB_PASSWORD")),
            "host": str(os.getenv("FALKORDB_HOST")),
            "port": int(os.getenv("FALKORDB_PORT")),
            "db": int(os.getenv("FALKORDB_USERMEM_DB", 10)),
        }
