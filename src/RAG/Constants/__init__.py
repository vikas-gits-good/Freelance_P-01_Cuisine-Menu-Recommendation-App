from glob import glob
from dataclasses import dataclass


@dataclass
class RAGCypherConstants:
    ALL_CYPHER_CODE_PATH = glob("src/RAG/Constants/*.cyp")


@dataclass
class SystemPromptConstants:
    SYSTEM_PROMPTS_TEXT_PATH = glob("src/RAG/Prompts/txt/*.txt")
