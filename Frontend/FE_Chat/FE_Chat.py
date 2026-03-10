import reflex as rx

from .Chat import ChatState, chat_page

app = rx.App(stylesheets=["/style.css"])
app.add_page(
    chat_page,
    route="/",
    on_load=ChatState.on_load,  # type:ignore
)
