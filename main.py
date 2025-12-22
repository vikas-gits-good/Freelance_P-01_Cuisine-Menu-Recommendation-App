import asyncio
from src.ETL.ETL_Utils import RestaurantData


if __name__ == "__main__":
    clean_data = asyncio.run(RestaurantData().get())
