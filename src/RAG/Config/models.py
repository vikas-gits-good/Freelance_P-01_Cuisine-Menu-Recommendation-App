import os
from typing import Literal
from dotenv import load_dotenv


class get_api_key:
    def __init__(self):
        self.groq = self._get_api_key("groq")
        self.opai = self._get_api_key("opai")

    def _get_api_key(self, source: Literal["groq", "opai"] = "groq"):
        load_dotenv("src/Secrets/RAG.env")
        api_key = {
            "groq": os.getenv("GROQ_API_KEY", ""),
            "opai": os.getenv("OPENAI_API_KEY", ""),
        }.get(source, os.getenv("GROQ_API_KEY", ""))
        return api_key


class ModelConfig:
    def __init__(self):
        self.api_key = get_api_key()
