import os
from dataclasses import dataclass


@dataclass
class ETLCyphersConstants:
    KG_NAME_PROD = "PROD_KG"
    KG_NAME_DEVL = "DEVL_KG"
    KG_NAME_TEST = "TEST_KG"
    __cpu_cnt = 0 if os.cpu_count() is None else os.cpu_count()
    NUMBER_OF_MT_WORKERS = __cpu_cnt
