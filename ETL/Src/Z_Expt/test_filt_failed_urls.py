import os

from Src.Config import MongoDBConfig
from Src.Constants import MDBIndexKey
from Src.Utils import pull_from_mongodb

mg_cnf = MongoDBConfig()

prev_data = pull_from_mongodb(  # old urls
    database=mg_cnf.swiggy.database,
    collection=mg_cnf.swiggy.coll_rstn_cnfg,
    idx_key=MDBIndexKey.RESTAURANT_CITY,
    city=os.getenv("SEEDER_CITY", "bangalore"),
    limit=0,
    prefix="Seeder",
)
print(f"Prev Len {len(prev_data['bangalore']['restaurants'])}")

fail_data = pull_from_mongodb(  # failed urls
    database=mg_cnf.swiggy.database,
    collection=mg_cnf.swiggy.coll_upst_fail,
    idx_key=MDBIndexKey.RESTAURANT_CITY,
    city=os.getenv("SEEDER_CITY", "bangalore"),
    limit=0,
    prefix="Seeder",
)
print(f"Fail Len {len(fail_data['bangalore'])}")


old_data = {}  # old urls that succeeded
for _city in prev_data.keys():
    all_urls = {rstn["rstn_url"] for rstn in prev_data[_city]["restaurants"]}
    print(len(all_urls))
    fail_urls = {rstn["url"] for rstn in fail_data[_city]}
    print(len(fail_urls))
    old_data[_city] = {
        "restaurants": [{"rstn_url": url} for url in (all_urls - fail_urls)],
    }
# print(old_data)

print(f"Old Len {len(old_data['bangalore']['restaurants'])}")
