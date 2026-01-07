import os
from glob import glob
from dotenv import load_dotenv
from dataclasses import dataclass
from src.Utils.main_utils import read_cypher


@dataclass
class FalkorDBConstants:
    load_dotenv("src/Secrets/Database.env")
    FALKORDB_USERNAME = os.getenv("FALKORDB_USERNAME")
    FALKORDB_PASSWORD = os.getenv("FALKORDB_PASSWORD")
    FALKORDB_HOST = os.getenv("FALKORDB_HOST")
    FALKORDB_HOST_PORT = os.getenv("FALKORDB_HOST_PORT")
    FALKORDB_CNTR_PORT = os.getenv("FALKORDB_CNTR_PORT")
    FALKORDB_CONNECTION_URI = f"redis://{FALKORDB_USERNAME}:{FALKORDB_PASSWORD}@{FALKORDB_HOST}:{FALKORDB_HOST_PORT}"


@dataclass
class CypherConstants:
    ALL_CYPHER_FILE_PATHS = glob("src/RAG/Cyphers/*.cyp")
