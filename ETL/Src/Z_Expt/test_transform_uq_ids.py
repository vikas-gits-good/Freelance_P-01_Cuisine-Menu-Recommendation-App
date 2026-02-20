import sys
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from Src.Config import MongoDBConfig
from Src.Constants import MDBIndexKey
from Src.Utils import LogException, log_etl, pull_from_mongodb

lctn_files: Dict[str, list[Dict[str, Any]]] = {
    "Country": [],
    "State": [],
    "City": [],
}
md_cnf = MongoDBConfig()
coll_dict = {
    MDBIndexKey.UNIQUE_COUNTRY: md_cnf.swiggy.coll_uq_cr_ids,
    MDBIndexKey.UNIQUE_STATE: md_cnf.swiggy.coll_uq_st_ids,
    MDBIndexKey.UNIQUE_CITY: md_cnf.swiggy.coll_uq_ct_ids,
}

for lctn, (idx_key, coll) in zip(lctn_files.keys(), coll_dict.items()):
    try:
        _data = pull_from_mongodb(
            database=md_cnf.swiggy.database,
            collection=coll,
            idx_key=idx_key,
            prefix="Loader",
        )
        for val in _data.values():
            lctn_files[lctn].append(val)

    except Exception as e:
        LogException(e, logger=log_etl)
        continue

print(lctn_files)

# "/home/who/Documents/Coding/Freelance_Projects/Freelance_P-01_Cuisine-Menu-Recommendation-App/ETL/Src/Z_Expt/test_transform_uq_ids.py" /home/who/Documents/Coding/Freelance_Projects/Freelance_P-01_Cuisine-Menu-Recommendation-App/ETL/.venv/bin/python -m test_transform_uq_ids.py
# /home/who/Documents/Coding/Freelance_Projects/Freelance_P-01_Cuisine-Menu-Recommendation-App/ETL/.venv/bin/python /home/who/Documents/Coding/Freelance_Projects/Freelance_P-01_Cuisine-Menu-Recommendation-App/ETL/Src/Z_Expt/test_transform_uq_ids.py
