import reflex as rx
from pydantic import BaseModel


class MessageStyle(BaseModel):
    display: str = "inline-block"
    padding: str = "0.5em"
    border_radius: str = "15px"
    max_width: list[str] = ["50em", "50em", "50em", "50em", "50em", "50em"]


class ChatMessage(BaseModel):
    message: str
    is_bot: bool = False


class ChatState(rx.State):
    DID_SUBMT: bool = False
    CONVO_HIST: list[ChatMessage] = []

    @rx.var
    def user_form_submit(self) -> bool:
        return self.DID_SUBMT

    def clear_gui(self):
        self.DID_SUBMT = False
        self.CONVO_HIST = []

    def on_load(self):
        self.clear_gui()

    def handle_submit(self, form_data: dict = {}):
        user_message = form_data.get("HumanMessage", "")
        if user_message:
            self.DID_SUBMT = True
            self.append_message_to_gui(user_message, False)
            yield

            # gpt_msgs = self.get_ai_messages()

            # llm_rspn = llm_response(gpt_msgs)

            self.DID_SUBMT = False
            # self.append_message_to_gui(llm_rspn, True)
            yield

    def rag_request(self, user_message):
        try:
            ...
            pass



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
