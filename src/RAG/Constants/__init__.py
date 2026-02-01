from glob import glob
from dataclasses import dataclass


@dataclass
class RAGCypherConstants:
    ALL_CYPHER_CODE_PATH = glob("src/RAG/Constants/*.cyp")
