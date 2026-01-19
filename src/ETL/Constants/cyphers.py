from glob import glob
from dataclasses import dataclass


@dataclass
class ETLCyphersConstants:
    ALL_CYPHER_FILE_PATHS = glob("src/ETL/Cyphers/*.cyp")
