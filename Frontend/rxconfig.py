import reflex as rx

config = rx.Config(
    app_name="FE_Chat",
    backend_host="0.0.0.0",
    backend_port=10001,
    frontend_port=10011,
    api_url="http://localhost:10001",
    deploy_url="http://localhost:10011",
    telemetry_enabled=False,
    state_auto_setters=False,
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ],
)
