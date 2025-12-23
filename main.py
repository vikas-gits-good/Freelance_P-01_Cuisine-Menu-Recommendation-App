import asyncio
from src.ETL.ETL_Utils import AllLinks, CityCoordinates, RestaurantData


if __name__ == "__main__":
    # # Get full sitemap of Swiggy
    _ = AllLinks().get()

    # get coordinates of cities
    _ = CityCoordinates().get()

    # # Get restaurant data based on location
    # clean_data = asyncio.run(RestaurantData().get())
