# syntax=docker/dockerfile:1.7

FROM ghcr.io/astral-sh/uv:python3.13-alpine3.23

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

ARG RAILWAY_SERVICE_ID=3da6f436-e4e2-4483-a6c0-5933a9030475
# ARG PORT=9001


# 1️⃣ Copy only dependency files (maximizes Docker cache)
COPY pyproject.toml uv.lock ./

# 2️⃣ Install dependencies (cached) /root/cache/uv
RUN --mount=type=cache,id=s/${RAILWAY_SERVICE_ID}-/root/cache/uv,target=/root/.cache/uv \
    uv sync --frozen --no-install-project


# 3️⃣ Copy application code AFTER dependencies
COPY . .


# 4️⃣ Install the project itself (fast, since deps already cached)
RUN --mount=type=cache,id=s/${RAILWAY_SERVICE_ID}-/root/cache/uv,target=/root/.cache/uv \
    uv sync --frozen

# Expose port
# EXPOSE 9001

CMD ["sh","-c","uv run uvicorn app:app --host 0.0.0.0 --port 9001"]
