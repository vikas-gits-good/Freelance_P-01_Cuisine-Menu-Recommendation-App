import os

from dotenv import load_dotenv


class ModelConfig:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("GROQ_API_KEY", "")
