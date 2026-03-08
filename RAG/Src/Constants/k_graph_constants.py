from dataclasses import dataclass


@dataclass
class FalkorDBConstants:
    CONNECTION_URI = "falkor://{user}:{pswd}@{host}:{port}"
