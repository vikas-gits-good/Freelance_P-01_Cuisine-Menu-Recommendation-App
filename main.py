import asyncio
from src.ETL.Utils import AllLinks, CityCoordinates, RestaurantData
from src.ETL.Components.load import Loader


if __name__ == "__main__":
    # # Get full sitemap of Swiggy
    # _ = AllLinks().get()

    # # get coordinates of cities
    # _ = CityCoordinates(task="proxy").get()

    # create browser instances
    # asyncio.run(GenerateBrowsers().start())
    # RestaurantData().get()

    Loader(purpose="test").run()
    pass
