import asyncio
from src.ETL.ETL_Utils import RestaurantData, AllLinks


if __name__ == "__main__":
    # Get restaurant data based on location
    # clean_data = asyncio.run(RestaurantData().get())

    # Get full sitemap of Swiggy
    # _ = AllLinks().get()
    _ = AllLinks().get_data_from_url()
