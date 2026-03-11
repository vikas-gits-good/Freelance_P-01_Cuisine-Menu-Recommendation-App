import os
from typing import Optional

import httpx
import reflex as rx
from dotenv import load_dotenv
from pydantic import BaseModel
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed


class ChatMessage(BaseModel):
    message: str
    is_bot: bool = False


class ChatState(rx.State):
    DID_SUBMT: bool = False
    CONVO_HIST: list[ChatMessage] = []
    load_dotenv()
    RAG_API_URL = os.getenv("RAG_API_URL", "")
    THREAD_ID: Optional[str] = None
    CURRENT_INPUT: str = ""

    @rx.var
    def user_form_submit(self) -> bool:
        return self.DID_SUBMT

    def set_CURRENT_INPUT(self, value: str):
        self.CURRENT_INPUT = value

    def clear_gui(self):
        self.DID_SUBMT = False
        self.CONVO_HIST = []

    def on_load(self):
        self.clear_gui()

    @rx.event(background=True)
    async def handle_submit(self, form_data: dict = {}):
        try:
            user_message = form_data.get("HumanMessage", "")
            if user_message:
                async with self:
                    self.DID_SUBMT = True
                    self.append_message_to_gui(user_message, False)

                llm_rspn = await self.rag_api_call(user_message)

                async with self:
                    self.DID_SUBMT = False
                    self.append_message_to_gui(llm_rspn, True)

        except Exception as e:
            raise e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(5),
        retry=retry_if_exception_type(
            (httpx.ConnectError, httpx.TimeoutException, httpx.RemoteProtocolError)
        ),
        reraise=True,
    )
    async def rag_api_call(self, message: str):
        payload = {"message": message, "thread_id": self.THREAD_ID}
        async with httpx.AsyncClient() as client:
            res = await client.post(
                f"{self.RAG_API_URL}/chat", json=payload, timeout=60
            )
            data = res.json()
        async with self:
            self.THREAD_ID = data.get("thread_id", None)

        return data["reply"]

    def append_message_to_gui(
        self,
        message,
        is_bot: bool = False,
    ):
        self.CONVO_HIST.append(
            ChatMessage(
                message=message,
                is_bot=is_bot,
            )
        )
