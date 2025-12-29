from dataclasses import dataclass


@dataclass
class MongoDBConstats:
    CONNECTION_URI = (
        "mongodb://{username}:{password}@localhost:27017/mongodb-local?authSource=admin"
    )

    @dataclass
    class swiggy_cnsts:
        DATABASE_NAME = "Swiggy_Data"
        COLLECTION_SITEMAP = "01_Full_Sitemap"
        COLLECION_RESTAURANT_CONFIG = "02_Restaurant_Config"
        COLLECTION_RESTAURANT_MENU = "03_Restaurant_Menu_JSON"
