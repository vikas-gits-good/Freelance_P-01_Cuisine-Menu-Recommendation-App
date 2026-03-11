import os

import reflex as rx
from dotenv import load_dotenv

load_dotenv()

RAILWAY_PUBLIC_DOMAIN = os.getenv("RAILWAY_PUBLIC_DOMAIN", "")
LOCAL_DOMAIN = os.getenv("LOCAL_DOMAIN", "127.0.0.1")

if RAILWAY_PUBLIC_DOMAIN:
    api_url = f"https://{RAILWAY_PUBLIC_DOMAIN}/backend"
    deploy_url = f"https://{RAILWAY_PUBLIC_DOMAIN}"

else:
    api_url = f"http://{LOCAL_DOMAIN}:10001"
    deploy_url = f"http://{LOCAL_DOMAIN}:10011"


config = rx.Config(
    app_name="FE_Chat",
    backend_host="0.0.0.0",
    backend_port=10001,
    frontend_port=10011,
    api_url=api_url,
    deploy_url=deploy_url,
    telemetry_enabled=False,
    state_auto_setters=False,
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ],
)
