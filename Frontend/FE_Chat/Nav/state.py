import reflex as rx


class NavState(rx.State):
    @staticmethod
    def to_chat() -> rx.event.EventSpec:
        return rx.redirect("/")
