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

    # Loader().run()
    pass

from src.ETL.Constants.cyphers import NodeLabels
from typing import Dict, Any

data = {
    NodeLabels.COUNTRY: [],
    NodeLabels.STATE: [],
    NodeLabels.CITY: [],
    NodeLabels.AREA: [],
    NodeLabels.LOCALITY: [],
}

data = {
    NodeLabels.COUNTRY.value: [],
    NodeLabels.STATE.value: [],
    NodeLabels.CITY.value: [],
    NodeLabels.AREA.value: [],
    NodeLabels.LOCALITY.value: [],
}


def printer(data: Dict[NodeLabels, Any]):
    for name, val in data.items():
        if name == NodeLabels.COUNTRY:
            print(NodeLabels.COUNTRY.value)
