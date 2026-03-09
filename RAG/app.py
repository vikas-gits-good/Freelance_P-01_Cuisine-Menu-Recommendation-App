from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from Src.Components import GRState, runner
from Src.Config import ChatRequest, ChatResponse
from Src.Utils import LogException, log_rag


@asynccontextmanager
async def lifespan(app: FastAPI):
    log_rag.info("GRAG: Initialising LangGraphState")
    runner.initialize()  # build graph once at startup
    yield
    log_rag.info("GRAG: Shutting down")


app = FastAPI(title="RAG", lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # lock this down in production
    allow_methods=["POST"],
    allow_headers=["*"],
)


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    try:
        thread_id = req.thread_id or str(uuid4())
        result: GRState = await runner.invoke(req.message, thread_id)
        messages = result.messages
        last_message: str = messages[-1].content if messages else "No response"  # type: ignore
        response = ChatResponse(reply=last_message, thread_id=thread_id)

    except Exception as e:
        LogException(e, logger=log_rag)
        response = ChatResponse(
            reply="Error processing query. Try again", thread_id=thread_id
        )

    return response


@app.get("/health")
async def health():
    return {"status": "ok"}
