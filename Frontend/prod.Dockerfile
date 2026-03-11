# syntax=docker/dockerfile:1.7
FROM ghcr.io/astral-sh/uv:python3.13-trixie-slim

ARG PORT=10011
ENV PORT=$PORT \
    REFLEX_REDIS_URL=redis://localhost \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    caddy \
    redis-server \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

COPY . .

RUN uv run reflex init
RUN uv run reflex export --frontend-only --no-zip && mv .web/build/client/* /srv/ && rm -rf .web

STOPSIGNAL SIGKILL
EXPOSE $PORT

CMD ["sh", "-c", "caddy start && redis-server --daemonize yes && exec uv run reflex run --env prod --backend-only"]
