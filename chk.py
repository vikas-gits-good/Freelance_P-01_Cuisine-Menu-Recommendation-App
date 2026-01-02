from src.Utils.main_utils import read_json, get_from_mongodb
from src.Config import MongoDBConfig

mc = MongoDBConfig()

path = "./src/ETL/ETL_Data/sitemap/final_menu_data_1.json"

data_dict = read_json(path)

city_data = get_from_mongodb(
    database=mc.swiggy.database,
    collection=mc.swiggy.coll_rstn_menu,
)


for i, rstn in enumerate(data_dict["bengaluru"]["restaurants"]):
    if "menu" in rstn.keys():
        city_data["bengaluru"]["restaurants"][i] = rstn
