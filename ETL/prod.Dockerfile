# syntax=docker/dockerfile:1.7

FROM ghcr.io/astral-sh/uv:python3.13-trixie-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-install-project && \
    uv run playwright install chromium --with-deps && \
    rm -rf /var/lib/apt/lists/* /tmp/*

COPY . .

CMD ["uv", "run", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]
