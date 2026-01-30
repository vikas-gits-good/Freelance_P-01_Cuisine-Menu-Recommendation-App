from glob import glob
from dataclasses import dataclass


@dataclass
class RAGCypherConstants:
    ALL_CYPHER_CODE_PATH = "src/RAG/Constants/tools_code.cyp"
    ALL_CYPHER_COLS_PATH = "src/RAG/Constants/tools_cols.json"
