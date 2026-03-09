import asyncio
from uuid import uuid4

from falkordb.asyncio import FalkorDB as AsyncFalkorDB

from Src.Config import ChatRequest, ChatResponse, FalkorDBConfig
from Src.Utils import LogException, log_rag

from .runner import GraphRunner
from .state import GRState


def execute_chat(request: ChatRequest, runner: GraphRunner):
    try:
        thread_id = request.thread_id or str(uuid4())
        result: GRState = await runner.invoke(req.message, thread_id)
        messages = result.messages
        last_message: str = (
            messages[-1].content if messages else "No response from system."
        )  # type: ignore
        response = ChatResponse(reply=last_message, thread_id=thread_id)

    except Exception as e:
        LogException(e, logger=log_rag)
        response = ChatResponse(
            reply="Error processing query. Try again",
            thread_id=thread_id,
        )

    return response  # .model_dump()


async def execute_health():
    """Async health check - pings all dependencies in parallel for faster response."""
    status = {"status": "ok", "falkor": "ok"}

    async def check_falkor():
        try:
            fd_cnf = FalkorDBConfig()
            fdb = AsyncFalkorDB(**fd_cnf.conn_dict, socket_timeout=5)
            graph = fdb.select_graph(fd_cnf.fdb_kg)
            await graph.query("RETURN 1")

        except Exception as e:
            log_rag.info("RAG_API: Health check FAIL (FalkorDB)")
            LogException(e, logger=log_rag)
            status["falkor"] = "unreachable"
            status["status"] = "degraded"

    # Run all health checks in parallel
    await asyncio.gather(
        check_falkor(),
        return_exceptions=True,  # Continue even if one fails
    )

    return status
