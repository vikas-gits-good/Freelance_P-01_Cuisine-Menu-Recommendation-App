import reflex as rx

from FE_Chat.Nav import NavState


def navbar_link(text: str, url: str) -> rx.Component:
    return rx.link(
        rx.text(
            text,
            size="4",
            weight="medium",
            id="navbar-link-text",
        ),
        href=url,
        id="navbar-link",
    )


def base_navbar() -> rx.Component:
    return rx.box(
        rx.desktop_only(
            rx.hstack(
                rx.hstack(
                    rx.image(
                        src="/logo.jpg",
                        width="2.25em",
                        height="auto",
                        border_radius="25%",
                        id="navbar-logo",
                    ),
                    rx.heading(
                        "Restaurant Competitor Analysis app",
                        size="7",
                        weight="bold",
                        id="navbar-heading",
                    ),
                    align_items="center",
                ),
                rx.hstack(
                    navbar_link("Chat", "/"),
                    justify="end",
                    spacing="5",
                ),
                justify="between",
                align_items="center",
            ),
        ),
        rx.mobile_and_tablet(
            rx.hstack(
                rx.hstack(
                    rx.image(
                        src="/logo.jpg",
                        width="2em",
                        height="auto",
                        border_radius="25%",
                        id="navbar-logo",
                    ),
                    rx.heading(
                        "Restaurant Competitor Analysis app",
                        size="6",
                        weight="bold",
                        id="navbar-heading",
                    ),
                    align_items="center",
                ),
                rx.menu.root(
                    rx.menu.trigger(rx.icon("menu", size=30)),
                    rx.menu.content(
                        rx.menu.item("Chat", on_click=NavState.to_chat()),
                    ),
                    justify="end",
                ),
                justify="between",
                align_items="center",
            ),
        ),
        bg=rx.color("accent", 3),
        padding="1em",
        # position="fixed",
        # top="0px",
        # z_index="5",
        width="100%",
    )
