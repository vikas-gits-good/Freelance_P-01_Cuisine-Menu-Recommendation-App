from dataclasses import dataclass
from glob import glob


@dataclass
class RAGCypherConstants:
    ALL_CYPHER_CODE_PATH = glob("Src/Constants/Cyphers/*.cyp")


@dataclass
class SystemPromptConstants:
    SYSTEM_PROMPTS_TEXT_PATH = glob("Src/Constants/Prompts/*.txt")
