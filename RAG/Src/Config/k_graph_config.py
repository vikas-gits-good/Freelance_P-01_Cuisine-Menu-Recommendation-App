import os
from urllib.parse import quote

from dotenv import load_dotenv

from Src.Constants import FalkorDBConstants


class FalkorDBConfig:
    """Method to get credentials to connect to a FalkorDB instance"""

    def __init__(self):
        load_dotenv(".env")
        # self.conn_uri = FalkorDBConstants.CONNECTION_URI.format(
        #     user=quote(str(os.getenv("ETL_FALKOR_USER"))),
        #     pswd=quote(str(os.getenv("ETL_FALKOR_PSWD"))),
        #     host=quote(str(os.getenv("ETL_FALKOR_HOST"))),
        #     port=quote(str(os.getenv("ETL_FALKOR_PORT"))),
        # )
        self.conn_dict = {
            # "username": str(os.getenv("ETL_FALKOR_USER")),
            # "password": str(os.getenv("ETL_FALKOR_PSWD")),
            "host": str(os.getenv("ETL_FALKOR_HOST")),
            "port": int(os.getenv("ETL_FALKOR_PORT", "6379")),
        }
        self.fdb_kg = os.getenv("ETL_FALKOR_DABA", "PROD_KG")
