# syntax=docker/dockerfile:1.7

FROM ghcr.io/astral-sh/uv:python3.13-alpine3.23

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-install-project

COPY . .

CMD ["sh","-c","uv run uvicorn app:app --host 0.0.0.0 --port 9001"]
