import reflex as rx

from .state import ChatState


def chat_form() -> rx.Component:
    return rx.form(
        rx.vstack(
            rx.text_area(
                name="HumanMessage",
                placeholder="Type your message",
                required=True,
                width="100%",
            ),
            rx.button(
                "Submit",
                type="submit",
                id="chat-button-submit",
            ),
        ),
        on_submit=ChatState.handle_submit,
        reset_on_submit=True,
    )
