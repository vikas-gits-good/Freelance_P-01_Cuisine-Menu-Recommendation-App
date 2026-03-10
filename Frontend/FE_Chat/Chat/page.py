import reflex as rx

from FE_Chat.GUI import base_layout

from .form import chat_form
from .state import ChatMessage, ChatState


def message_box(chat_message: ChatMessage):
    return rx.box(
        rx.box(
            rx.box(
                rx.markdown(
                    chat_message.message,
                    background_color=rx.cond(
                        chat_message.is_bot,
                        rx.color("mauve", 4),
                        rx.color("blue", 4),
                    ),
                    color=rx.cond(
                        chat_message.is_bot,
                        rx.color("mauve", 12),
                        rx.color("blue", 12),
                    ),
                    padding="0.5em",
                    border_radius="15px",
                ),
                class_name="markdown-table",
                display=rx.cond(chat_message.is_bot, "block", "inline-block"),
                max_width=rx.cond(chat_message.is_bot, "100%", "50em"),
                overflow_x="auto",
                background_color=rx.cond(
                    chat_message.is_bot,
                    rx.color("mauve", 4),
                    rx.color("blue", 4),
                ),
                border_radius="15px",
            ),
            text_align=rx.cond(chat_message.is_bot, "left", "right"),
            width="100%",
        ),
        width="100%",
    )


def chat_page() -> rx.Component:
    return base_layout(
        rx.vstack(
            rx.box(
                rx.foreach(
                    ChatState.CONVO_HIST,
                    message_box,
                ),
                width="100%",
            ),
            chat_form(),
            margin="3rem auto",
            spacing="5",
            justify="center",
            min_height="85vh",
        )
    )
