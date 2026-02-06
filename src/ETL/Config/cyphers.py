import os
import re
from typing import Literal
from dotenv import load_dotenv
from src.Utils.main_utils import read_cypher
from src.ETL.Constants.cyphers import ETLCyphersConstants


class get_cypher_code:
    def __init__(self):
        self.all_cyp_paths = ETLCyphersConstants.ALL_CYPHER_FILE_PATHS
        self.create = self.get_code(code="create")
        self.upsert = self.get_code(code="upsert")
        self.validate = self.get_code(code="validate")

    def get_code(self, code: Literal["create", "upsert", "validate"] = "create"):
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


class ETLCypherConfig:
    def __init__(self):
        load_dotenv("src/Secrets/Database.env")  # ../../../
        FALKORDB_USERNAME = os.getenv("FALKORDB_USERNAME")
        FALKORDB_PASSWORD = os.getenv("FALKORDB_PASSWORD")
        FALKORDB_HOST = os.getenv("FALKORDB_HOST")
        FALKORDB_PORT = os.getenv("FALKORDB_PORT")

        self.cp_code = get_cypher_code()
        self.auth_params = {
            "username": str(FALKORDB_USERNAME),
            "password": str(FALKORDB_PASSWORD),
            "host": str(FALKORDB_HOST),
            "port": int(FALKORDB_PORT),
        }
