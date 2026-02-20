from Src.Config import MongoDBConfig, Restaurant
from Src.Constants import MDBIndexKey
from Src.Utils import pull_from_mongodb

md_cnf = MongoDBConfig()
collections = [
    [
        md_cnf.swiggy.coll_uq_ct_ids,
        md_cnf.swiggy.coll_uq_st_ids,
        md_cnf.swiggy.coll_uq_cr_ids,
        md_cnf.swiggy.coll_ms_ct_nam,
        md_cnf.swiggy.coll_rstn_cnfg,
        md_cnf.swiggy.coll_scrp_data,
        md_cnf.swiggy.coll_upst_fail,
    ],
    [
        MDBIndexKey.UNIQUE_CITY,
        MDBIndexKey.UNIQUE_STATE,
        MDBIndexKey.UNIQUE_COUNTRY,
        MDBIndexKey.UNIQUE_CITY,
        MDBIndexKey.RESTAURANT_CITY,
        [MDBIndexKey.RESTAURANT_ID, MDBIndexKey.RESTAURANT_CITY],
        [MDBIndexKey.RESTAURANT_ID, MDBIndexKey.RESTAURANT_CITY],
    ],
    [
        "all",
        "bangalore",
    ],
]


data = pull_from_mongodb(
    database=md_cnf.swiggy.database,
    collection=collections[0][5],
    idx_key=collections[1][5][1],
    city=collections[2][1],
    limit=2,
)
# print(data)

for item in data["bangalore"]:
    rstn = Restaurant(**item["data"])
    print(rstn)
