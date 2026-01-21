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

from src.ETL.Config.cyphers import ETLCypherConfig
from src.ETL.Constants.cyphers import NodeLabels, IndexName

ecc = ETLCypherConfig()

# Build lookup from lowercase label name to actual NodeLabel
label_lookup = {label.value.lower(): label.value for label in NodeLabels}

query_list = []
for index_name in IndexName:
    parts = index_name.value.split("_")
    label_key = parts[0]  # "country", "subcuisine", etc.
    id_type = parts[1]  # "ids" or "name"

    query = ecc.cp_code.create.get("create_index", "").format(
        index_name=index_name.value,
        index_label=label_lookup[label_key],
        index_id=id_type,
    )
    query_list.append(query)
