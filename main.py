import asyncio

from src.ETL.Components.load import Loader
from src.ETL.Utils import AllLinks, CityCoordinates, RestaurantData
from src.RAG.Components.graph import LangGraphState

if __name__ == "__main__":
    # # Get full sitemap of Swiggy
    # _ = AllLinks().get()

    # # get coordinates of cities
    # _ = CityCoordinates(task="proxy").get()

    # create browser instances
    # asyncio.run(GenerateBrowsers().start())
    # RestaurantData().get()

    # Loader(purpose="test").run()
    pass


# from src.ETL.Config.graph_pool import GraphPool

# graph = GraphPool.get_graph(graph_name="test")

# query = """
# MATCH (c:City {name: 'Bengaluru'})-[:HAS_AREA]-(area:Area {name: 'Banasawadi'})
# MATCH (area)-[HAS_LOCALITY]-()-[:HAS_RESTAURANT]-(rstn:Restaurant)
# MATCH (rstn)-[SERVES_MAIN_CUISINE]-(cuis:MainCuisine)
# RETURN DISTINCT cuis.name
# """

# data = graph.query(query).result_set
# data
