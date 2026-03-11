import os

import reflex as rx
from dotenv import load_dotenv

load_dotenv()

config = rx.Config(
    app_name="FE_Chat",
    backend_host="0.0.0.0",
    backend_port=10001,
    frontend_port=10011,
    api_url=os.getenv("RAG_APP_URL", "http://localhost"),
    deploy_url=os.getenv("RAG_APP_URL", "http://localhost"),
    telemetry_enabled=False,
    state_auto_setters=False,
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ],
)
