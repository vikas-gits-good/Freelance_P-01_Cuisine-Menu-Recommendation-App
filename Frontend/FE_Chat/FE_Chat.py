import reflex as rx

from .GUI import base_layout

app = rx.App()
app.add_page(base_layout, route="/")
