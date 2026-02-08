import asyncio
from src.ETL.Utils import AllLinks, CityCoordinates, RestaurantData
from src.ETL.Components.load import Loader
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


from src.RAG.User.Components.memory import UserMemory

um = UserMemory()
# um.create_indexes()

# graph = um._pool.acquire()
# try:
#     result = graph.query("CALL db.indexes()")
#     for row in result.result_set:
#         print(row)
# finally:
#     um._pool.release(graph)
