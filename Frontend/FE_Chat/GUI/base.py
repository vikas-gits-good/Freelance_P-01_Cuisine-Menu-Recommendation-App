import reflex as rx

from .navbar import base_navbar


def base_layout(*args, **kwargs) -> rx.Component:
    return rx.container(
        base_navbar(),
        rx.fragment(
            *args,
            **kwargs,
            id="base-fragment",
        ),
        id="base-container",
    )
