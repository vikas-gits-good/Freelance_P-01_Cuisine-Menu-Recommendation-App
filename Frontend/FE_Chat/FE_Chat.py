"""Welcome to Reflex! This file outlines the steps to create a basic app."""

import reflex as rx

from . import Chat, Navigation, Pages

app = rx.App()
app.add_page(Pages.home, route=Navigation.Routes.HOME)
app.add_page(Pages.about, route=Navigation.Routes.ABOUT)
app.add_page(
    Chat.chat_page,
    route=Navigation.Routes.CHAT,
    on_load=Chat.ChatState.on_load,  # type:ignore
)
app.add_page(
    Chat.chat_page,
    route=f"{Navigation.Routes.CHAT}/[sesn_id]",
    on_load=Chat.ChatState.on_detail_load,  # type:ignore
)
