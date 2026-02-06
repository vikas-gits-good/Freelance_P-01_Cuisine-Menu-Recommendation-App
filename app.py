from src.RAG.Components.graph import LangGraphState


def build_graph():
    lgs = LangGraphState()
    return lgs.build()


graph = build_graph()
