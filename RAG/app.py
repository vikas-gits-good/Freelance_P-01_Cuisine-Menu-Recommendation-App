import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from Src.Components import execute_chat, execute_health, runner
from Src.Config import ChatRequest, ChatResponse
from Src.Utils import log_rag


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
async def chat(request: ChatRequest):
    return execute_chat(request, runner)


@app.get("/health")
async def health():
    return asyncio.run(execute_health())
