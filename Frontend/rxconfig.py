import reflex as rx

config = rx.Config(
    app_name="FE_Chat",
    backend_host="127.0.0.1",
    backend_port=10001,
    frontend_port=11001,
    api_url="http://127.0.0.1:10001",
    deploy_url="http://0.0.0.0:11001",
    telemetry_enabled=False,
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ],
)
