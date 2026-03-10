import reflex as rx

from .state import ChatState


def chat_form() -> rx.Component:
    return rx.form(
        rx.vstack(
            rx.el.textarea(
                name="HumanMessage",
                placeholder="Type your message",
                required=True,
                width="100%",
                value=ChatState.CURRENT_INPUT,
                on_change=ChatState.set_CURRENT_INPUT,
                enter_key_submit=True,
                rows="3",
                style={
                    "padding": "0.75em",
                    "border_radius": "8px",
                    "border": "1px solid #444",
                    "background_color": "#1e1e1e",
                    "color": "#fff",
                    "font_size": "1em",
                    "width": "100%",
                    "resize": "none",
                    "outline": "none",
                },
            ),
            # rx.text_area(
            #     name="HumanMessage",
            #     placeholder="Type your message",
            #     required=True,
            #     width="100%",
            # ),
            rx.button(
                "Submit",
                type="submit",
                id="chat-button-submit",
            ),
        ),
        on_submit=ChatState.handle_submit,
        reset_on_submit=True,
    )
