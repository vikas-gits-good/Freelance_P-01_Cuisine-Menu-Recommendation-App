# syntax=docker/dockerfile:1.7
FROM ghcr.io/astral-sh/uv:python3.13-trixie-slim AS builder

ARG RAILWAY_PUBLIC_DOMAIN
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

RUN apt-get update && apt-get install -y unzip curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project
COPY . .
RUN uv run reflex init && \
    mkdir -p /srv && \
    uv run reflex export --frontend-only --no-zip && \
    mv .web/build/client/* /srv/ && \
    rm -rf .web

FROM caddy:2.11 AS caddy
COPY Caddyfile /etc/caddy/Caddyfile
RUN caddy fmt --overwrite /etc/caddy/Caddyfile

FROM ghcr.io/astral-sh/uv:python3.13-trixie-slim

ARG RAILWAY_PUBLIC_DOMAIN
ARG PORT=10011
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=$PORT \
    PATH="/app/.venv/bin:$PATH"

RUN apt-get update && apt-get install -y parallel && rm -rf /var/lib/apt/lists/*

COPY --from=builder /srv /srv
COPY --from=builder /app /app
COPY --from=caddy /etc/caddy/Caddyfile /etc/caddy/Caddyfile
COPY --from=caddy /usr/bin/caddy /usr/bin/caddy

WORKDIR /app

STOPSIGNAL SIGKILL
EXPOSE $PORT

CMD ["parallel", "--ungroup", "--halt", "now,fail=1", ":::", \
     "uv run reflex run --backend-only --env prod", \
     "caddy run --config /etc/caddy/Caddyfile 2>&1"]
