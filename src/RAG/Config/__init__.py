import re
from src.RAG.Constants import FalkorDBConstants


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
