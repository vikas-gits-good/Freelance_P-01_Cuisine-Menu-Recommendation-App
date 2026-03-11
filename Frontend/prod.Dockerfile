# syntax=docker/dockerfile:1.7

FROM ghcr.io/astral-sh/uv:python3.13-trixie-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    REFLEX_REDIS_URL=redis://localhost

WORKDIR /app

RUN apt-get update && apt-get install -y \
    redis-server \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-install-project

COPY . .

RUN uv run reflex init

RUN uv run reflex export --frontend-only --no-zip

STOPSIGNAL SIGKILL

CMD ["sh", "-c", "redis-server --daemonize yes && exec uv run reflex run --env prod --backend-host 0.0.0.0 --backend-port 10001 --frontend-port 10011"]
