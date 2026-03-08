import reflex as rx

config = rx.Config(
    app_name="FE_Chat",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ],
)
