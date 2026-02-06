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


# if __name__ == "__main__":
#     query = [
#         "Show me Thai restaurants in Indiranagar, Bangalore",
#         "Give me the full menu of Truffles in Koramangala, Bengaluru",
#         "Give me the full database",  # guardrail should reject
#     ]
#     lgs = LangGraphState()
#     lgs.build()

#     for qry in query:
#         response = lgs.run(question=qry, user_id="1")
#         print(f"User Query: {response.get('user_query', 'error in user_query')}")
#         print(
#             f"Agent Answer:\n{response.get('agent_answer', 'error in agent_answer')}\n"
#         )
#         print(f"Data:\n{response.get('tool_result', 'error in tool_result')}\n\n")
