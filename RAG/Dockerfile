# syntax=docker/dockerfile:1.7

FROM ghcr.io/astral-sh/uv:python3.13-alpine3.23

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app


# 1️⃣ Copy only dependency files (maximizes Docker cache)
COPY pyproject.toml uv.lock ./

# 2️⃣ Install dependencies (cached)
RUN --mount=type=cache,id=cache-uv,target=/root/.cache/uv \
    uv sync --frozen --no-install-project


# 3️⃣ Copy application code AFTER dependencies
COPY . .


# 4️⃣ Install the project itself (fast, since deps already cached)
RUN --mount=type=cache,id=cache-uv,target=/root/.cache/uv \
    uv sync --frozen


EXPOSE 9001

CMD ["sh","-c","uv run uvicorn app:app --host 0.0.0.0 --port ${PORT:-9001}"]
