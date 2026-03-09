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
            rx.hstack(
                rx.button(
                    "Submit",
                    type="submit",
                    id="chat-button-submit",
                ),
                rx.cond(
                    ChatState.user_form_submit,
                    rx.text(
                        "Submitted.",
                        size="3",
                    ),
                    rx.fragment(),
                ),
            ),
        ),
        on_submit=ChatState.handle_submit,
        reset_on_submit=False,
    )
